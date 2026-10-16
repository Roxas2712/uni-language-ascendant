#include <stdint.h>
#include <stddef.h>
// Match a complete decompressed prefix; reject invalid back references.
int scan(const uint8_t*r,int rn,const uint8_t*t,int tn,int*result){
 uint8_t out[32768];int count=0;
 for(int start=0;start<rn;start++){
  int p=start,n=0,ok=1;
  while(p<rn && n<tn && ok){
   int h=r[p++];if(h==255){ok=0;break;} int c=h>>5,l=(h&31)+1;
   if(c==7){if(p>=rn)break;c=(h>>2)&7;l=((h&3)<<8)+r[p++]+1;}
   int a=0,b=0,from=0;
   if(c==1||c==2){if(p>=rn)break;a=r[p++];if(c==2){if(p>=rn)break;b=r[p++];}}
   if(c>=4){if(p>=rn)break;a=r[p++];if(a&128)from=n-(a&127)-1;else{if(p>=rn)break;from=a*256+r[p++];}}
   for(int k=0;k<l && n<tn;k++){
    int v=0;
    if(c==0){if(p>=rn){ok=0;break;}v=r[p++];}
    else if(c==1)v=a;else if(c==2)v=(k&1)?b:a;
    else if(c>=4){int idx=from+(c==6?-k:k);if(idx<0||idx>=n){ok=0;break;}v=out[idx];if(c==5){v=((v&0x55)<<1)|((v&0xaa)>>1);v=((v&0x33)<<2)|((v&0xcc)>>2);v=(v<<4|v>>4)&255;}}
    if(v!=t[n]){ok=0;break;}out[n++]=v;
   }
  }
  if(ok&&n==tn){result[count++]=start;if(count>=32)return count;}
 }
 return count;
}
int tile(const uint8_t*r,int rn,const uint8_t*t,int*pal){
 for(int s=0;s+16<=rn;s++){
  int p[4]={-1,-1,-1,-1},ok=1;
  for(int y=0;y<8&&ok;y++)for(int x=0;x<8;x++){
   int v=((r[s+y*2]>>(7-x))&1)+2*((r[s+y*2+1]>>(7-x))&1),c=t[y*8+x];
   if(p[v]<0)p[v]=c;else if(p[v]!=c){ok=0;break;}
  }
  if(ok){for(int k=0;k<4;k++)pal[k]=p[k];return s;}
 }
 return -1;
}
