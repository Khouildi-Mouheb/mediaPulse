import requests, time
start=time.time()
print('Sending request...')
with open('scripts/test_audio.wav', 'wb') as f: f.write(b'RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x80>\x00\x00\x00}\x00\x00\x02\x00\x10\x00data\x00\x00\x00\x00')
res=requests.post('http://127.0.0.1:8001/detect-media', data={'user_id':1, 'timestamp':'2025'}, files={'audio': open('scripts/test_audio.wav', 'rb')})
print(f'Time: {time.time()-start:.2f}s')
print(res.status_code, res.text)
