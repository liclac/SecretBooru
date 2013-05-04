import io, base64
from Crypto.Cipher import AES
from Crypto import Random

def dencrypt(data, outpath, key = None):
	print "Encrypting to %s" % outpath
	bs = AES.block_size
	if key is None:
		key = Random.new().read(16)
	else:
		key = base64.b64decode(key)
	iv = Random.new().read(bs)
	encryptor = AES.new(key, AES.MODE_CBC, iv)
	print "Key: %s" % base64.b64encode(key)
	print "IV: %s" % base64.b64encode(iv)

	fin = io.BytesIO(data)
	fout = io.BytesIO()
	
	fout.write(iv)
	while True:
		chunk = fin.read(bs*1024)
		if len(chunk) == 0:
			break
		elif len(chunk) % bs != 0:
			chunk += b' ' * (bs - len(chunk) % bs)
		fout.write(encryptor.encrypt(chunk))

	with open(outpath, 'wb') as f:
		f.write(fout.getvalue())
	
	return base64.b64encode(key)

def ddecrypt(key, inpath):
	print "Decrypting %s" % inpath
	print "Key: %s" % key
	bs = AES.block_size
	
	fout = io.BytesIO()
	with open(inpath, 'rb') as fin:#, open(out_file, 'wb') as fout:
		iv = fin.read(bs)
		print "IV: %s" % base64.b64encode(iv)
		decryptor = AES.new(base64.b64decode(key), AES.MODE_CBC, iv)
		
		while True:
			chunk = fin.read(bs*1024)
			if len(chunk) == 0:
				break
			fout.write(decryptor.decrypt(chunk))
	return fout.getvalue()
