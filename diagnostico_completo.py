"""
Script de Diagnóstico Completo - GetMyHouse
Identifica exatamente por que não encontra propriedades.

Uso: python diagnostico_completo.py
"""

import sys
from pathlib import Path

print("=" * 80)
print("🔍 DIAGNÓSTICO COMPLETO - GetMyHouse")
print("=" * 80)
print()

# Step 1: Check imports
print("📦 Step 1: Verificando imports...")
try:
    from src.tools.mock_search_tool import MockSearchTool
    from src.config import MockDataConfig, SearchConfig
    print("✅ Imports OK")
except Exception as e:
    print(f"❌ ERRO nos imports: {e}")
    print("\n💡 Solução: Verificar que está na pasta do projeto")
    sys.exit(1)

# Step 2: Check configuration
print("\n📋 Step 2: Verificando configuração...")
print(f"  PROPERTIES_PER_CITY: {MockDataConfig.PROPERTIES_PER_CITY}")
print(f"  MOCK_CITIES: {len(MockDataConfig.MOCK_CITIES)} cidades")
print(f"  MOCK_AGENCIES: {len(MockDataConfig.MOCK_AGENCIES)} agências")
print(f"  Expected total: {MockDataConfig.PROPERTIES_PER_CITY * len(MockDataConfig.MOCK_CITIES)}")

if MockDataConfig.PROPERTIES_PER_CITY != 30:
    print(f"⚠️  WARNING: PROPERTIES_PER_CITY deveria ser 30, não {MockDataConfig.PROPERTIES_PER_CITY}")
    print("   Versão antiga do ficheiro config.py!")

# Step 3: Generate properties
print("\n🏗️  Step 3: Gerando propriedades...")
tool = MockSearchTool()
all_props = tool.get_all_properties()
print(f"  Total geradas: {len(all_props)}")

if len(all_props) != 300:
    print(f"❌ ERRO: Deveria ter 300 propriedades, tem {len(all_props)}")
    print("   Versão antiga do ficheiro mock_search_tool.py!")
else:
    print("✅ Quantidade correta de propriedades")

# Step 4: Check Lisboa distribution
print("\n📍 Step 4: Verificando distribuição em Lisboa...")
lisboa_props = [p for p in all_props if p['city'] == 'Lisboa']
print(f"  Total em Lisboa: {len(lisboa_props)}")

lisboa_flats = [p for p in lisboa_props if p['type'] == 'flat']
lisboa_houses = [p for p in lisboa_props if p['type'] == 'house']
print(f"  Flats: {len(lisboa_flats)}")
print(f"  Houses: {len(lisboa_houses)}")

# Check typology distribution
from collections import Counter
flat_types = Counter([p['typology'] for p in lisboa_flats])
print(f"\n  Flats por tipologia:")
for typ in ['T0', 'T1', 'T2', 'T3', 'T4', 'T4+']:
    count = flat_types.get(typ, 0)
    print(f"    {typ}: {count}")

if flat_types.get('T2', 0) < 2 or flat_types.get('T3', 0) < 2:
    print("⚠️  WARNING: Poucas propriedades T2/T3!")
    print("   Distribuição não está balanceada - versão antiga!")

# Step 5: Test actual search
print("\n🔍 Step 5: Testando busca real...")
print("  Parâmetros:")
print("    Location: Lisboa")
print("    Property Type: flat")
print("    Typology: ['T2', 'T3']")
print("    Price: 0 - 500.000")

search_results = tool.search(
    location='Lisboa',
    property_type='flat',
    typology=['T2', 'T3'],
    price_min=0,
    price_max=500000
)

print(f"\n  Resultado: {len(search_results)} propriedades")

if len(search_results) == 0:
    print("❌ ERRO CRÍTICO: Nenhuma propriedade encontrada!")
    print("\n🔎 Investigando passo a passo...")
    
    # Debug step by step
    step1 = [p for p in all_props if 'Lisboa' in p.get('location', '') or p.get('city') == 'Lisboa']
    print(f"    Após filtro location: {len(step1)}")
    
    step2 = [p for p in step1 if p.get('type') == 'flat']
    print(f"    Após filtro type=flat: {len(step2)}")
    
    step3 = [p for p in step2 if p.get('typology') in ['T2', 'T3']]
    print(f"    Após filtro T2/T3: {len(step3)}")
    
    step4 = [p for p in step3 if p.get('price', 0) <= 500000]
    print(f"    Após filtro price≤500k: {len(step4)}")
    
    if len(step4) > 0:
        print("\n📊 Propriedades que deveriam aparecer:")
        for p in step4[:3]:
            print(f"      {p['typology']} - €{p['price']:,} - {p['location']}")
        print("\n⚠️  As propriedades existem mas a função search() não as encontra!")
        print("   Problema no código de filtragem do mock_search_tool.py")
    else:
        print("\n⚠️  Realmente não há propriedades que satisfaçam os critérios!")
        print("   Problema na geração de dados")
    
    sys.exit(1)
else:
    print("✅ Busca funcionou!")
    print(f"\n📊 Amostra de resultados:")
    for i, p in enumerate(search_results[:3], 1):
        print(f"  {i}. {p['typology']} - €{p['price']:,}")
        print(f"     {p['location']}")
        print(f"     {p['agency']} | {p['state']}")

# Step 6: Test with broader criteria
print("\n🔍 Step 6: Testando com critérios amplos...")
broad_results = tool.search(
    location='Lisboa',
    price_max=1000000
)
print(f"  Lisboa (sem filtros): {len(broad_results)} propriedades")

if len(broad_results) == 0:
    print("❌ ERRO: Mesmo sem filtros não encontra nada!")
    print("   Problema grave no mock_search_tool.py")
    sys.exit(1)

# Step 7: Summary
print("\n" + "=" * 80)
print("📊 SUMÁRIO")
print("=" * 80)

all_ok = True

checks = [
    ("Config correto", MockDataConfig.PROPERTIES_PER_CITY == 30),
    ("300 propriedades geradas", len(all_props) == 300),
    ("30 props em Lisboa", len(lisboa_props) == 30),
    ("15 flats em Lisboa", len(lisboa_flats) == 15),
    ("Busca funciona", len(search_results) > 0),
]

for check_name, check_ok in checks:
    icon = "✅" if check_ok else "❌"
    print(f"{icon} {check_name}")
    if not check_ok:
        all_ok = False

print("=" * 80)

if all_ok:
    print("\n🎉 TUDO OK! Sistema funcionando corretamente.")
    print("\nSe ainda vê 'No properties found' no Streamlit:")
    print("1. Para o Streamlit (Ctrl+C)")
    print("2. Apaga cache: streamlit cache clear")
    print("3. Apaga __pycache__: Get-ChildItem -Recurse __pycache__ | Remove-Item -Recurse -Force")
    print("4. Reinicia: streamlit run app.py")
    sys.exit(0)
else:
    print("\n❌ PROBLEMAS ENCONTRADOS!")
    print("\n💡 SOLUÇÃO:")
    print("1. Tens ficheiros ANTIGOS")
    print("2. Precisa re-extrair getmyhouse_v1_4_FIXED.zip")
    print("3. APAGAR pasta getmyhouse completamente primeiro")
    print("4. Depois extrair ZIP fresco")
    sys.exit(1)
