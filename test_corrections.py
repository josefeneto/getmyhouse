"""
Script de Teste Automatizado - GetMyHouse v1.2

Valida se todas as correções foram aplicadas corretamente.

Author: José Neto
Date: November 2024
"""

import sys
from pathlib import Path


def test_distance_label():
    """Testa se o campo Distance tem '(km)' no label."""
    print("🔍 Teste 1: Verificar label 'Distance to Location (km)'...")
    
    app_file = Path("app.py")
    if not app_file.exists():
        print("   ❌ Ficheiro app.py não encontrado!")
        return False
    
    with open(app_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if 'Distance to Location (km)' in content:
        print("   ✅ Label correto encontrado!")
        return True
    else:
        print("   ❌ Label '(km)' NÃO encontrado!")
        print("   Procurar por: 'Distance to Location (km)'")
        return False


def test_no_generation_config():
    """Verifica se não há uso de generation_config nos agents."""
    print("\n🔍 Teste 2: Verificar ausência de generation_config...")
    
    agents_dir = Path("src/agents")
    if not agents_dir.exists():
        print("   ❌ Diretório src/agents não encontrado!")
        return False
    
    problem_files = []
    
    for py_file in agents_dir.glob("*.py"):
        if py_file.name == "__init__.py":
            continue
            
        with open(py_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                # Ignorar comentários
                if line.strip().startswith('#'):
                    continue
                
                if 'generation_config' in line and 'LlmAgent' in line:
                    problem_files.append((py_file.name, line_num, line.strip()))
    
    if not problem_files:
        print("   ✅ Nenhum uso de generation_config encontrado!")
        return True
    else:
        print("   ❌ Problemas encontrados:")
        for filename, line_num, line in problem_files:
            print(f"      {filename}:{line_num} - {line[:60]}...")
        return False


def test_verify_script_exists():
    """Verifica se o script de verificação existe."""
    print("\n🔍 Teste 3: Verificar script verify_adk_compliance.py...")
    
    verify_file = Path("verify_adk_compliance.py")
    if verify_file.exists():
        print("   ✅ Script de verificação encontrado!")
        return True
    else:
        print("   ❌ Script verify_adk_compliance.py NÃO encontrado!")
        return False


def test_readme_exists():
    """Verifica se o README de correções existe."""
    print("\n🔍 Teste 4: Verificar documentação README_CORRECOES.md...")
    
    readme_file = Path("README_CORRECOES.md")
    if readme_file.exists():
        print("   ✅ Documentação encontrada!")
        return True
    else:
        print("   ⚠️  README_CORRECOES.md não encontrado (opcional)")
        return True  # Não é crítico


def test_imports():
    """Testa se os imports estão corretos."""
    print("\n🔍 Teste 5: Verificar imports dos agents...")
    
    try:
        # Tenta importar config
        sys.path.insert(0, str(Path.cwd()))
        from src.config import ADKConfig
        print("   ✅ Import de config funcionou!")
        
        # Verifica se MODEL_NAME existe
        if hasattr(ADKConfig, 'MODEL_NAME'):
            print(f"   ✅ MODEL_NAME configurado: {ADKConfig.MODEL_NAME}")
        else:
            print("   ❌ MODEL_NAME não encontrado em ADKConfig!")
            return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erro ao importar: {str(e)}")
        return False


def run_all_tests():
    """Executa todos os testes."""
    print("=" * 80)
    print("🧪 GetMyHouse v1.2 - Teste de Correções")
    print("=" * 80)
    print()
    
    tests = [
        ("Distance Label", test_distance_label),
        ("No generation_config", test_no_generation_config),
        ("Verify Script", test_verify_script_exists),
        ("Documentation", test_readme_exists),
        ("Imports", test_imports),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"   ❌ Erro durante teste: {str(e)}")
            results.append((test_name, False))
    
    print("\n" + "=" * 80)
    print("📊 Resumo dos Testes:")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        icon = "✅" if result else "❌"
        print(f"{icon} {test_name}")
    
    print("\n" + "-" * 80)
    print(f"Total: {passed}/{total} testes passaram")
    
    if passed == total:
        print("\n🎉 Todas as correções foram aplicadas com sucesso!")
        print("✅ Projeto está pronto para execução")
        return 0
    else:
        print(f"\n⚠️  {total - passed} teste(s) falharam")
        print("Verificar README_CORRECOES.md para instruções")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
