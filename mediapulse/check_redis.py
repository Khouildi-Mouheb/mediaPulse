#!/usr/bin/env python
"""Script pour checker le contenu de Redis"""
import redis
import json
import sys

def check_redis():
    try:
        # Connexion à Redis
        r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        
        # Test de connexion
        r.ping()
        print("✅ Connecté à Redis\n")
        
        # 1. Vérifier les clés live_text (textes du flux YouTube)
        print("=" * 70)
        print("📻 TEXTES DU FLUX YOUTUBE EN REDIS")
        print("=" * 70)
        
        text_keys = r.keys("mediapulse:live_text:*")
        if text_keys:
            print(f"✅ Trouvé {len(text_keys)} chaînes avec textes:\n")
            for key in text_keys:
                entries = r.lrange(key, 0, 5)  # Les 5 dernières entrées
                print(f"\n🔑 Clé: {key}")
                print(f"   Nombre d'entrées: {r.llen(key)}")
                if entries:
                    for i, entry in enumerate(entries):
                        try:
                            data = json.loads(entry)
                            print(f"   [{i}] {data['timestamp']}: {data['text'][:80]}...")
                        except:
                            print(f"   [{i}] Erreur parsing JSON")
        else:
            print("❌ AUCUNE CLÉE TROUVÉE! Redis est vide!")
        
        # 2. Vérifier les clés de statut
        print("\n" + "=" * 70)
        print("🔴 STATUT DES WORKERS")
        print("=" * 70)
        
        status_keys = r.keys("mediapulse:live_status:*")
        if status_keys:
            for key in status_keys:
                status_json = r.get(key)
                if status_json:
                    status = json.loads(status_json)
                    print(f"\n📊 {status['name']}:")
                    print(f"   Worker running: {status.get('worker_running')}")
                    print(f"   Last chunk: {status.get('last_chunk_time')}")
                    print(f"   Last error: {status.get('last_error', 'None')}")
        else:
            print("❌ Aucun statut trouvé")
        
        # 3. Afficher toutes les clés pour debug
        print("\n" + "=" * 70)
        print("🔍 TOUTES LES CLÉS REDIS")
        print("=" * 70)
        
        all_keys = r.keys("mediapulse:*")
        if all_keys:
            print(f"Trouvé {len(all_keys)} clés:")
            for key in all_keys:
                key_type = r.type(key)
                if key_type == "list":
                    length = r.llen(key)
                    print(f"  • {key} (LIST, {length} items)")
                elif key_type == "string":
                    length = len(r.get(key))
                    print(f"  • {key} (STRING, {length} bytes)")
                else:
                    print(f"  • {key} ({key_type})")
        else:
            print("❌ Redis complètement vide!")
        
        # 4. Vérifier la config
        print("\n" + "=" * 70)
        print("⚙️ CONFIG REDIS")
        print("=" * 70)
        try:
            info = r.info()
            print(f"Version: {info.get('redis_version')}")
            print(f"Mode: {info.get('redis_mode')}")
            print(f"Clients connectés: {info.get('connected_clients')}")
            print(f"Mémoire utilisée: {info.get('used_memory_human')}")
            print(f"Nombre de clés: {info.get('db0', {}).get('keys', 'N/A') if 'db0' in info else r.dbsize()}")
        except Exception as e:
            print(f"Erreur: {e}")
            
    except redis.ConnectionError as e:
        print(f"❌ ERREUR: Impossible de se connecter à Redis sur localhost:6379")
        print(f"   {e}")
        print(f"\n   Assurez-vous que Redis est en cours d'exécution:")
        print(f"   - Sur Windows: redis-server.exe")
        print(f"   - Docker: docker run -d -p 6379:6379 redis")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False
    
    return True

if __name__ == "__main__":
    check_redis()
