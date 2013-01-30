import base64

def chunks(l, n):
    return (l[i:i+n] for i in xrange(0, len(l), n))

def RSA_KEY_DER_to_PEM(data):
    a = ["-----BEGIN RSA PRIVATE KEY-----"]
    a.extend(chunks(base64.b64encode(data),64))
    a.append("-----END RSA PRIVATE KEY-----")
    return "\n".join(a)

def CERT_DER_to_PEM(data):
    a = ["-----BEGIN CERTIFICATE-----"]
    a.extend(chunks(base64.b64encode(data),64))
    a.append("-----END CERTIFICATE-----")
    return "\n".join(a)