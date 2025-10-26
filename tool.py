import argparse
import struct

u32le = lambda x: struct.unpack('<I', x)[0]
p32le = lambda x: struct.pack('<I', x)

def export_to_txt(asr_path: str, txt_path: str) -> None:
    with open(asr_path, 'rb') as f:
        # 8 Header 1 (Asura   )
        # 4 - Header 2 (HTXT)
        # 4 - Archive Length [+24]
        # 8 - Version (0)
        f.seek(24)
        # 4 - number of text strings
        num_files = u32le(f.read(4))
        # unknown
        f.seek(12, 1)
        
        texts: list[str] = []
        
        for _ in range(num_files):
            # 4 unknown
            hash: int = u32le(f.read(4))
            # 4 - string len [*2 for unicode] (including null-terminators)
            text_len: int = u32le(f.read(4)) - 1
            
            # X - Text String (unicode text)
            text: str = f.read(text_len * 2).decode('utf-16-le').rstrip('\x00').replace('\n', '\\n')
            # 2 - null filename terminator
            f.seek(2, 1)
            
            texts.append(text)
    
    with open(txt_path, 'w', encoding='UTF-8') as f:
        f.write('\n'.join(texts))
            
    
def import_from_txt(orig_file_path: str, txt_path: str, asr_path: str) -> None:
    with open(txt_path, 'r', encoding='UTF-8') as f:
        # the new length of the texts    
        texts = [line.rstrip('\n').replace('\\n', '\n') for line in f.readlines()]
        new_texts_len = sum(map(lambda e: len(e) + 1, texts))
        
    with open(orig_file_path, 'rb') as f:
            
        header = bytearray(f.read(40))
        # immediately add the new length of the texts
        archive_len = u32le(header[12:16]) + new_texts_len
        num_files = u32le(header[24:28])
        
        hashes: list[int] = []
        # skip text section to get to tail
        for _ in range(num_files):
            hash = u32le(f.read(4))
            hashes.append(hash)
            
            text_len = u32le(f.read(4)) - 1
            # subtract the old length of the texts
            archive_len -= text_len
            
            # skip text and null terminator
            f.seek(2 + text_len * 2, 1)
        
        header[12:16] = p32le(archive_len)
        
        tail = f.read()
        
    with open(asr_path, 'wb') as f:
        f.write(header)
        for index, text in enumerate(texts):
            text_bytes = text.encode('utf-16-le')
            text_len = len(text) + 1
            # 4 - hash
            f.write(p32le(hashes[index]))
            # 1 - string len
            f.write(p32le(text_len))
            # 2 * text_len
            f.write(text_bytes)
            f.write(b'\x00\x00') # null terminator
        f.write(tail) # write back tail with keys
        
   
        
def main() -> None:
    ap = argparse.ArgumentParser(description='Sniper Elite 3 localization tool')
    sub = ap.add_subparsers(dest='cmd', required=True)
    
    exp = sub.add_parser('export', help='asr → txt')
    exp.add_argument('asr')
    exp.add_argument('txt')
    
    imp = sub.add_parser('import', help='txt → asr')
    imp.add_argument('original')
    imp.add_argument('txt')
    imp.add_argument('asr')
    
    args = ap.parse_args()
    if args.cmd == 'export':
        export_to_txt(args.asr, args.txt)
    else:
        import_from_txt(args.original, args.txt, args.asr)
    
if __name__ == '__main__':
    main()