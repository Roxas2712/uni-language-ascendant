"""Bounded Game Boy LZ3 decoder for verified graphics recipes."""
def decompress(data, start=0, limit=32768):
    p=start;out=bytearray()
    def byte():
        nonlocal p
        if p>=len(data):raise ValueError('Truncated LZ3 stream')
        value=data[p];p+=1;return value
    while True:
        h=byte()
        if h==255:return bytes(out),p-start
        command=h>>5;n=(h&31)+1
        if command==7:command=(h>>2)&7;n=((h&3)<<8)+byte()+1
        if command>6:raise ValueError('Invalid LZ3 command')
        if len(out)+n>limit:raise ValueError('LZ3 output exceeds limit')
        if command==0:out.extend(byte() for _ in range(n))
        elif command==1:out.extend([byte()]*n)
        elif command==2:
            a,b=byte(),byte();out.extend(a if i%2==0 else b for i in range(n))
        elif command==3:out.extend(bytes(n))
        else:
            a=byte();source=len(out)-(a&127)-1 if a&128 else a*256+byte()
            for k in range(n):
                at=source-k if command==6 else source+k
                if at<0 or at>=len(out):raise ValueError('Invalid LZ3 back reference')
                value=out[at]
                if command==5:value=int(f'{value:08b}'[::-1],2)
                out.append(value)
