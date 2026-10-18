"""Authored engine fallback text; repeated fields keep source order."""
ROWS=r'''OAK: {PLAYER}!\nThis isn't the\vtime to use that!|オーキド: {PLAYER}！\nいまは つかうときではない！|오박사: {PLAYER}!\n지금은 쓸 때가 아니란다!
Give a nickname to\nthe {STRBUF} you\nreceived?|もらった {STRBUF}に\nニックネームを つけますか？|받은 {STRBUF}에게\n별명을 지어 줄까?
Placing third was\n%s,\fwho caught a\n%s!|３いは %s！\fつかまえた ポケモンは\n%s！|3위는 %s!\f잡은 포켓몬은\n%s!
Placing second was\n%s,\fwho caught a\n%s!|２いは %s！\fつかまえた ポケモンは\n%s！|2위는 %s!\f잡은 포켓몬은\n%s!
This Bug-Catching\nContest winner is\f%s,\nwho caught a\n%s!|むしとりたいかいの\nゆうしょうしゃは……\f%s！\nつかまえたのは %s！|곤충채집 대회\n우승자는…\f%s!\n잡은 포켓몬은 %s!
It's {STRBUF}\nthat was left with\nthe DAY-CARE MAN.|そだてやの おじいさんに\nあずけた {STRBUF}だ！|키우미집 할아버지께\n맡긴 {STRBUF}이다!
It's {STRBUF}\nthat was left with\nthe DAY-CARE LADY.|そだてやの おばあさんに\nあずけた {STRBUF}だ！|키우미집 할머니께\n맡긴 {STRBUF}이다!
It has no interest\nin {STRBUF}.|{STRBUF}には\nきょうみが ないようだ|{STRBUF}에게는\n관심이 없는 것 같다
It appears to care\nfor {STRBUF}.|{STRBUF}を\nきにしているようだ|{STRBUF}을(를)\n신경 쓰는 것 같다
It's friendly with\n{STRBUF}.|{STRBUF}と\nなかが よいようだ|{STRBUF}와(과)\n사이가 좋은 것 같다
It shows interest\nin {STRBUF}.|{STRBUF}に\nきょうみが あるようだ|{STRBUF}에게\n관심이 있는 것 같다
Oh, make it forget\n{STRBUF}?|{STRBUF}を\nわすれさせますか？|{STRBUF}을(를)\n잊게 할까?
Hm… {STRBUF}?\nWhat a great name!\vIt's perfect.\fTreat {STRBUF}\nwith loving care.|ふむ…… {STRBUF}か！\nすばらしい なまえじゃ！\f{STRBUF}を\nたいせつに そだてておくれ|음… {STRBUF}인가!\n정말 멋진 이름이군!\f{STRBUF}을(를)\n소중하게 키워 주게
Hm… {STRBUF}…\nThat's a fairly\vdecent name.\fBut, how about a\nslightly better\vnickname?\fWant me to give it\na better name?|ふむ…… {STRBUF}か……\nなかなかの なまえじゃ\fだが もっと よい\nニックネームは どうじゃ？\fわしが よい なまえを\nつけてやろうか？|음… {STRBUF}인가…\n제법 괜찮은 이름이군\f하지만 더 좋은\n별명은 어떻겠나?\f내가 더 좋은 이름을\n지어 줄까?
All right. This\n#MON is now\vnamed {STRBUF}.|よし！ この ポケモンの\nなまえは {STRBUF}じゃ！|좋아! 이 포켓몬의\n이름은 {STRBUF}일세!
%d #MON seen\n%d #MON owned\fPROF.OAK's\nRating:|みつけたかず %dひき\nつかまえたかず %dひき\fオーキドはかせの\nひょうか:|발견한 수 %d마리\n잡은 수 %d마리\f오박사의\n평가:
Good. I see you\nunderstand how to\vuse # BALLS.|よし！ モンスターボールの\nつかいかたが わかったようじゃ|좋아! 몬스터볼을 쓰는 법을\n이해한 모양이구나
Have you met KURT?\nHis custom #\vBALLS should help.|ガンテツには あったかね？\nとくせいの ボールは\fきっと やくに たつじゃろう|강집을 만나 보았니?\n특제 몬스터볼이\f도움이 될 거란다
OK, I'll take care\nof your money.\f…|わかったわ おかねは\nあずかっておくわね\f……|알았어. 돈은\n맡아 둘게\f…
{PLAYER} received\n%s.|{PLAYER}は\n%sを もらった！|{PLAYER}는(은)\n%s을(를) 받았다!
{PLAYER} put the\n%s in\nthe %s.|{PLAYER}は\n%sを\f%sに しまった！|{PLAYER}는(은)\n%s을(를)\f%s에 넣었다!
Excuse me.\nYou're not ready.|すみません\nじゅんびが できていません|죄송합니다\n준비가 되어 있지 않습니다
Only three POKéMON\nmay be entered.|さんかできる ポケモンは\n３びき だけです|참가할 수 있는 포켓몬은\n3마리뿐입니다
The {STRBUF} POKéMON\nmust all be different kinds.|{STRBUF}びきの ポケモンは\nすべて ちがう しゅるいにします|{STRBUF}마리의 포켓몬은\n모두 다른 종류여야 합니다
The {STRBUF} POKéMON\nmust not hold the same items.|{STRBUF}びきの ポケモンに\nおなじ どうぐは もたせられません|{STRBUF}마리의 포켓몬에게\n같은 도구를 지니게 할 수 없습니다
You can't take an\nEGG!|タマゴは\nつれていけません！|알은\n데려갈 수 없습니다!
Please return when\nyou're ready.|じゅんびが できましたら\nまた おこしください|준비가 되면\n다시 와 주세요
Which prize would\nyou like?|どの けいひんに\nしますか？|어느 경품으로\n할까?
{STRBUF}?\nIs that right?|{STRBUF}で\nよろしいですか？|{STRBUF}으로\n괜찮을까?
Here you go!|はい どうぞ！|여기 있습니다!
You don't have\nenough points.|ポイントが\nたりません|포인트가\n부족합니다
Oh. Please come\nback again!|では また\nおこしください！|그럼 다시\n와 주세요!
I see all.\nI know all…\fCertainly, I know\nof your #MON!|わたしは すべてを みとおす\nすべてを しっている……\fもちろん あなたの\nポケモンの こともね！|나는 모든 것을 보고\n모든 것을 알고 있지…\f물론 네 포켓몬에\n대해서도 알고 있단다!
Whaaaat? I can't\ntell a thing!\fHow could I not\nknow of this?|なんと！ なにも わからない！\fわたしに わからないとは\nどういう ことだ？|뭐라고? 아무것도 모르겠어!\f내가 이것을 모르다니\n어떻게 된 거지?
Hm… I see you met\n%s here:\v%s!|ふむ…… %sとは\nここで であったのだね:\f%s！|음… %s와(과)\n여기서 만났구나:\f%s!
The time was\n%s!\fIts level was %s!\fAm I good or what?|じかんは %s！\fレベルは %sだった！\fどうだ すごいだろう？|시간은 %s!\f레벨은 %s였어!\f어때, 대단하지?
Hm… %s\ncame from %s\vin a trade?\f%s\nwas where %s\vmet %s!|ふむ…… %sは\n%sから こうかんで\fやってきたのだね？\f%sで\n%sが\f%sと であったのだ！|음… %s은(는)\n%s에게서 교환으로\f온 것이구나?\f%s에서\n%s이(가)\f%s와(과) 만났어!
What!? Incredible!\fI don't understand\nhow, but it is\fincredible!\nYou are special.\fI can't tell where\nyou met it, but it\vwas at level %s.\fAm I good or what?|なんと！ すばらしい！\fよくは わからないが\nあなたは とくべつだ！\fであった ばしょは\nわからないが\fレベルは %sだった！\fどうだ すごいだろう？|뭐라고? 놀랍구나!\f어떻게 된 건지는 몰라도\n너는 특별해!\f만난 장소는 모르겠지만\n레벨은 %s였어!\f어때, 대단하지?
Hey!\fThat's an EGG!\fYou can't say that\nyou've met it yet…|おや！\fそれは タマゴだ！\fまだ であったとは\nいえないね……|어이!\f그건 알이잖아!\f아직 만났다고는\n할 수 없겠구나…
Fufufu! I saw that\nyou'd do nothing!|ふふふ！ なにもしないことも\nおみとおしだったよ！|후후후! 아무것도 안 할 줄도\n이미 알고 있었지!
Incidentally…\fIt would be wise\nto raise your\f#MON with a\nlittle more care.|ところで……\fもうすこし たいせつに\nポケモンを そだてるといい|그런데…\f포켓몬을 조금 더\n소중하게 키워 주렴
Incidentally…\fIt seems to have\ngrown a little.\f%s seems\nto be becoming\vmore confident.|ところで……\fすこし せいちょうしたようだね\f%sは\nじしんが ついてきたようだ|그런데…\f조금 성장한 모양이구나\f%s은(는)\n자신감이 생기는 것 같아
Incidentally…\f%s has\ngrown. It's gained\vmuch strength.|ところで……\f%sは\nせいちょうしたね\fずいぶん つよくなった！|그런데…\f%s은(는)\n성장했구나\f아주 강해졌어!
Incidentally…\fIt certainly has\ngrown mighty!\fThis %s\nmust have come\fthrough numerous\n#MON battles.\fIt looks brimming\nwith confidence.|ところで……\fとても つよくなったね！\fこの %sは\nたくさんの しょうぶを\fけいけんしてきたようだ\nじしんに あふれているね|그런데…\f정말 강해졌구나!\f이 %s은(는)\n수많은 포켓몬 승부를\f겪어 온 모양이야\n자신감이 넘쳐 보여
Incidentally…\fI'm impressed by\nyour dedication.\fIt's been a long\ntime since I've\fseen a #MON as\nmighty as this\v%s.\fI'm sure that\nseeing %s\fin battle would\nexcite anyone.|ところで……\fあなたの ねっしんな\nそだてかたには かんしんしたよ\fこんなに つよい\n%sを みるのは\fほんとうに ひさしぶりだ\f%sの しょうぶは\nだれもが むちゅうに なるだろう|그런데…\f정성껏 키운 모습에\n감동했단다\f이렇게 강한\n%s을(를) 보는 것은\f정말 오랜만이야\f%s의 승부를 보면\n누구나 흥분하겠지
%s was sent to BILL's PC.|%sは\nマサキの パソコンへ おくられた|%s은(는)\n이수재의 컴퓨터로 보내졌다
Throw away %d\n%s(S)?|%dこ\n%sを すてますか？|%d개\n%s을(를) 버릴까?
may be seen around|で みられます|에서 볼 수 있습니다
{STRBUF} was\nsent to {STRBUF}.|{STRBUF}は\n{STRBUF}へ おくられた！|{STRBUF}은(는)\n{STRBUF}에게 보내졌다!
For {STRBUF}'s\n{STRBUF},|{STRBUF}の\n{STRBUF}の かわりに|{STRBUF}의\n{STRBUF} 대신
{STRBUF} sends\n{STRBUF}.|{STRBUF}は\n{STRBUF}を おくった！|{STRBUF}은(는)\n{STRBUF}을(를) 보냈다!
{STRBUF} bids\nfarewell to|{STRBUF}が おわかれするのは|{STRBUF}이(가) 작별할 상대는
Take good care of\n{STRBUF}.|{STRBUF}を\nかわいがってあげてね！|{STRBUF}을(를)\n잘 부탁해!
I collect #MON.\nDo you have\v{STRBUF}?\fWant to trade it\nfor my {STRBUF}?|ポケモンを あつめてるんだ\n{STRBUF}を もってる？\fぼくの {STRBUF}と\nこうかん しない？|포켓몬을 모으고 있어\n{STRBUF} 있어?\f내 {STRBUF}와(과)\n교환하지 않을래?
Huh? That's not\n{STRBUF}. What a letdown…|あれ？ {STRBUF}じゃ\nないじゃない ざんねん……|어? {STRBUF}이(가)\n아니잖아. 실망이야…
Yay! I got myself\n{STRBUF}!\vThanks!|やった！ {STRBUF}を\nてにいれた！ ありがとう！|야호! {STRBUF}을(를)\n얻었다! 고마워!
Hi, how's my old\n{STRBUF} doing?|ぼくの {STRBUF}は\nげんきに してる？|내 {STRBUF}은(는)\n잘 지내고 있어?
{PLAYER} traded\n{STRBUF} for\v{STRBUF}.|{PLAYER}は\n{STRBUF}を\f{STRBUF}と こうかんした！|{PLAYER}는(은)\n{STRBUF}을(를)\f{STRBUF}와(과) 교환했다!
{PLAYER} got on the\n{STRBUF}.|{PLAYER}は\n{STRBUF}に のった！|{PLAYER}는(은)\n{STRBUF}을(를) 탔다!
{PLAYER} got off\nthe {STRBUF}.|{PLAYER}は\n{STRBUF}から おりた！|{PLAYER}는(은)\n{STRBUF}에서 내렸다!
{STRBUF} used\nCUT!|{STRBUF}の\nいあいぎり！|{STRBUF}의\n풀베기!
{STRBUF} used\nSURF!|{STRBUF}の\nなみのり！|{STRBUF}의\n파도타기!
{STRBUF} used\nWATERFALL!|{STRBUF}の\nたきのぼり！|{STRBUF}의\n폭포오르기!
{STRBUF} used\nSTRENGTH!|{STRBUF}の\nかいりき！|{STRBUF}의\n괴력!
{STRBUF} can\nmove boulders.|{STRBUF}は\nいわを おせるようになった！|{STRBUF}은(는)\n바위를 밀 수 있게 되었다!
{STRBUF} used\nDIG!|{STRBUF}の\nあなをほる！|{STRBUF}의\n구멍파기!
{STRBUF} used\nWHIRLPOOL!|{STRBUF}の\nうずしお！|{STRBUF}의\n바다회오리!
{PLAYER} found\n{STRBUF}.|{PLAYER}は\n{STRBUF}を みつけた！|{PLAYER}는(은)\n{STRBUF}을(를) 발견했다!
{PLAYER} found\n{STRBUF}!|{PLAYER}は\n{STRBUF}を みつけた！|{PLAYER}는(은)\n{STRBUF}을(를) 발견했다!
But {PLAYER} can't\ncarry any more\vitems!|しかし {PLAYER}は\nどうぐを もてない！|하지만 {PLAYER}는(은)\n도구를 더 지닐 수 없다!
{STRBUF} did a\nHEADBUTT!|{STRBUF}の\nずつき！|{STRBUF}의\n박치기!
{STRBUF} used\nSWEET SCENT!|{STRBUF}の\nあまいかおり！|{STRBUF}의\n달콤한향기!
'''
def translations(language,keys):
 from asian_engine_ui import unescape
 return {unescape(r[0]):{'value':unescape(r[1 if language=='ja'else 2])}for line in ROWS.splitlines()if len(r:=line.split('|'))==3 and unescape(r[0])in keys}
