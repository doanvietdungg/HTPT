import httpx
import asyncio

async def test_concurrent_locks():
    """
    Simulate multiple clients trying to acquire an exclusive lock on the same file concurrently.
    """
    FILE_ID = "test-file-123"
    
    # 1. Register a test user
    async with httpx.AsyncClient() as client:
        try:
            await client.post("http://localhost:8000/api/auth/register", json={
                "username": "test_lock_user",
                "password": "password123",
                "full_name": "Test User"
            })
        except:
            pass # ignore if already exists
            
        # Login
        resp = await client.post("http://localhost:8000/api/auth/login", json={
            "username": "test_lock_user",
            "password": "password123"
        })
        token = resp.json().get("access_token")
        
    headers = {"Authorization": f"Bearer {token}"}
    
    async def try_acquire(client_id):
        print(f"Client {client_id} attempting to acquire EXCLUSIVE lock...")
        async with httpx.AsyncClient() as c:
            r = await c.post(
                f"http://localhost:8000/api/lock/acquire?file_id={FILE_ID}&client_id={client_id}&lock_type=EXCLUSIVE",
                headers=headers
            )
            print(f"Client {client_id} result: {r.status_code} - {r.text}")
            
    # Launch 5 concurrent clients
    tasks = [try_acquire(f"client_{i}") for i in range(1, 6)]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(test_concurrent_locks())
