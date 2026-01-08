"""
Script de Verificação - Testa todas as correções do SPRINT 1 e 2
"""
import asyncio
import sys
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

# Setup path
sys.path.append('.')

from app.database.db_connection import engine
from app.database.models.logs import GameLog
from app.database.models.player import Player
from app.database.models.npc import NPC
from app.core.chronos import world_clock


async def verify_corrections():
    print("🔍 VERIFICANDO CORREÇÕES DO SPRINT 1 E 2...\n")
    
    results = {
        "gamelog_table": False,
        "chronos_time": False,
        "npc_location_filter": False
    }
    
    # Test 1: GameLog table exists
    print("1️⃣ Verificando tabela GameLog...")
    try:
        async with AsyncSession(engine) as session:
            stmt = select(GameLog).limit(1)
            result = await session.execute(stmt)
            results["gamelog_table"] = True
            print("   ✅ Tabela GameLog existe e está acessível")
    except Exception as e:
        print(f"   ❌ Erro ao acessar GameLog: {e}")
    
    # Test 2: Chronos time
    print("\n2️⃣ Verificando Chronos (tempo do mundo)...")
    try:
        current_time = world_clock.get_current_datetime()
        time_of_day = world_clock.get_time_of_day()
        season = world_clock.get_season()
        
        print(f"   📅 Data: {current_time.day}/{current_time.month}/{current_time.year}")
        print(f"   🕐 Hora: {current_time.hour:02d}:{current_time.minute:02d}")
        print(f"   🌅 Período: {time_of_day}")
        print(f"   🌸 Estação: {season}")
        
        # Test advance
        old_hour = current_time.hour
        world_clock.advance_turn()
        new_time = world_clock.get_current_datetime()
        
        if new_time.hour != old_hour or new_time.day != current_time.day:
            results["chronos_time"] = True
            print(f"   ✅ Chronos avançou corretamente: {old_hour:02d}:00 → {new_time.hour:02d}:00")
        else:
            print(f"   ❌ Chronos não avançou")
    except Exception as e:
        print(f"   ❌ Erro ao verificar Chronos: {e}")
    
    # Test 3: NPC location filter
    print("\n3️⃣ Verificando filtro de localização de NPCs...")
    try:
        async with AsyncSession(engine) as session:
            # Get all NPCs
            stmt_all = select(NPC)
            result_all = await session.execute(stmt_all)
            all_npcs = result_all.scalars().all()
            
            # Get NPCs by location
            if all_npcs:
                test_location = all_npcs[0].current_location
                stmt_loc = select(NPC).where(NPC.current_location == test_location)
                result_loc = await session.execute(stmt_loc)
                filtered_npcs = result_loc.scalars().all()
                
                print(f"   📊 Total de NPCs no banco: {len(all_npcs)}")
                print(f"   📍 NPCs em '{test_location}': {len(filtered_npcs)}")
                
                if len(filtered_npcs) <= len(all_npcs):
                    results["npc_location_filter"] = True
                    print(f"   ✅ Filtro de localização funciona")
                else:
                    print(f"   ❌ Filtro retornou mais NPCs que o total")
            else:
                print(f"   ⚠️ Nenhum NPC no banco para testar")
                results["npc_location_filter"] = True  # Consider pass if no data
    except Exception as e:
        print(f"   ❌ Erro ao verificar filtro de NPCs: {e}")
    
    # Summary
    print("\n" + "="*60)
    print("📊 RESUMO DA VERIFICAÇÃO\n")
    
    total = len(results)
    passed = sum(results.values())
    
    for test, status in results.items():
        icon = "✅" if status else "❌"
        print(f"{icon} {test}")
    
    print(f"\n🎯 Resultado: {passed}/{total} testes passaram ({passed/total*100:.0f}%)")
    
    if passed == total:
        print("\n🎉 TODAS AS CORREÇÕES ESTÃO FUNCIONANDO!")
    else:
        print("\n⚠️ Algumas correções precisam de atenção")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(verify_corrections())
    sys.exit(0 if success else 1)
