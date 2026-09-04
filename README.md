# reelsindir.com Render backend

1. GitHub'da `reelsindir-backend` adlı yeni repo oluştur.
2. Bu ZIP içindeki dosyaları repo köküne yükle.
3. Render > New > Web Service > GitHub repo seç.
4. Dockerfile otomatik algılanmalı.
5. Deploy et.
6. `https://SERVIS-ADIN.onrender.com/health` aç. `{"ok":true}` görürsen çalışıyor.
7. Test için POST `/api/extract` ve JSON body:
   `{"url":"https://www.instagram.com/reel/ORNEK/"}`

Canlıya geçince Render Environment Variables içinde:
`CORS_ORIGINS=https://reelsindir.com`
olarak değiştir.

Not: Instagram bazı public içeriklerde bile login/cookie isteyebilir. Bu nedenle her Reels bağlantısının sürekli çalışacağı garanti edilemez.
