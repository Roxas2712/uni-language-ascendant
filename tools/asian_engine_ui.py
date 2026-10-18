"""Authored translations of actual recompiler UI strings, not ROM excerpts."""
import re
ROWS=r'''Zzz... Hm? Wha...?\nYou woke me up!\fWill you check the\nclock for me?|ぐう…… ん？ なんじゃ？\nめが さめてしまった！\fとけいを みてくれるかね？|쿨쿨... 음? 뭐라고?\n잠이 깼잖니!\f시계를 확인해 주겠니?
Enemy %s|あいての %s|상대의 %s
BOX%d|ボックス%d|박스%d
DECORATION|もようがえ|방 꾸미기
PLAYER %s|プレイヤー %s|플레이어 %s
OT/|おや/|어버이/
%s'S NEST|%sの ぶんぷ|%s의 분포
POKéMON Channel|ポケモンチャンネル|포켓몬 채널
Now on:|ほうそうちゅう:|방송 중:
ZEPHYR|ウイング|윙
HIVE|インセクト|인섹트
PLAIN|レギュラー|레귤러
FOG|ファントム|팬텀
STORM|ショック|쇼크
MINERAL|スチール|스틸
GLACIER|アイス|아이스
RISING|ライジング|라이징
BOULDER|グレー|그레이
CASCADE|ブルー|블루
THUNDER|オレンジ|오렌지
RAINBOW|レインボー|레인보우
SOUL|ピンク|핑크
MARSH|ゴールド|골드
VOLCANO|クりムゾン|크림슨
EARTH|グリーン|그린
 ALPH RUINS STAMP| アルフのいせきスタンプ| 알프 유적 스탬프
POKéRUS|ポケルス|포켓러스
OK|ふつう|정상
GEN 2|だい２せだい|２세대
DISPLAY (%dHZ)|がめん (%dHZ)|화면 (%dHZ)
PARKBALL×%02d|パークボール×%02d|파크볼×%02d
TM/HM|わざマシン|기술머신
SEL|えらぶ|선택
Lv%d|レベル%d|레벨%d
%s BED|%sのベッド|%s 침대
%s CARPET|%sのじゅうたん|%s 카펫
%s POSTER|%sのポスター|%s 포스터
%s DOLL|%sのぬいぐるみ|%s 인형
BIG %s|おおきな%s|큰 %s
Choose a POKéMON.|ポケモンを えらんでください|포켓몬을 골라 주세요
Choose a <PK><MN>.|ポケモンを えらんでください|포켓몬을 골라 주세요
Give a nickname to %s?|%sに
ニックネームを つけますか？|%s에게
별명을 지어 줄까?
Give a nickname to\n%s?|%sに
ニックネームを つけますか？|%s에게
별명을 지어 줄까?
No releasing EGGS!|タマゴは にがせません！|알은 놓아줄 수 없어!
What's up?|どうしますか？|무엇을 할까?
It's your last <PK><MN>!|さいごの ポケモンです！|마지막 포켓몬이야!
No more usable <PK><MN>!|たたかえる ポケモンが
いなくなります！|싸울 수 있는 포켓몬이
없어져!
Remove MAIL.|メールを はずしてください|메일을 떼어 주세요
There's no room!|あきが ありません！|빈자리가 없어!
Release <PK><MN>?|ポケモンを にがしますか？|포켓몬을 놓아줄까?
Released <PK><MN>.\fBye,\n%s!|ポケモンを にがした
ばいばい %s！|포켓몬을 놓아주었다
잘 가, %s!
Got %s!|%sを
ひきだした！|%s을(를)
데려왔다!
Stored %s!|%sを
あずけた！|%s을(를)
맡겼다!
There is no POKéMON there.|そこに ポケモンは いません|거기에 포켓몬은 없어
The BOX is full.|ボックスが いっぱいです|박스가 가득 찼어
You can't deposit\nthe last POKéMON!|さいごの ポケモンは
あずけられません！|마지막 포켓몬은
맡길 수 없어!
It's already there.|すでに そこに います|이미 거기에 있어
You'll need a\nPOKéMON to call\fwith.|よびだすには ポケモンが
ひつようです|부르려면 포켓몬이
필요해
Play with\n3 coins?|コイン３まいで
あそびますか？|동전 3개로
놀까?
Place\nyour bet|かける ところを
えらんでください|걸 곳을
골라 주세요
The cards\nshuffled.|カードを
きりなおしました|카드를
다시 섞었다
Darn…|ざんねん……|아깝다……
{PLAYER} turned on\nthe PC.|{PLAYER}は
パソコンの スイッチをいれた|{PLAYER}는(은)
컴퓨터의 전원을 켰다
%s's PC|%sの パソコン|%s의 컴퓨터
Use on which <PK><MN>?|どの ポケモンに つかいますか？|어느 포켓몬에게 쓸까?
Teach which <PK><MN>?|どの ポケモンに おしえますか？|어느 포켓몬에게 가르칠까?
To which <PK><MN>?|どの ポケモンに しますか？|어느 포켓몬으로 할까?
You have no <PK><MN>!|ポケモンを もっていません！|포켓몬이 없어!
There is a POKéMON\nholding MAIL.|メールを もった
ポケモンが います|메일을 지닌
포켓몬이 있어
Please remove the\nMAIL.|メールを
はずしてください|메일을
떼어 주세요
No <PK><MN> found!|ポケモンが みつかりません！|포켓몬을 찾을 수 없어!
Printed %s's\ndata!\f|%sの データを
いんさつしました！|%s의 데이터를
인쇄했다!
Printer error!\n%s|プリンターの エラー！
%s|프린터 오류!
%s
<PK><MN> are listed by\nevolution type.|しんかする じゅんに
ポケモンを ならべます|진화 순서대로
포켓몬을 나열합니다
official type.|ずかんばんごう じゅんです|도감 번호 순서입니다
<PK><MN> are listed\nalphabetically.|ABCじゅんに
ポケモンを ならべます|ABC 순서대로
포켓몬을 나열합니다
UNOWN are listed\nin catching order.|つかまえた じゅんに
アンノーンを ならべます|잡은 순서대로
안농을 나열합니다
Today's %s,\nNumber is %05d!|きょうは %s
ばんごうは %05d！|오늘은 %s
번호는 %05d!
OK, so you wanted\na %s?|%sで
いいですか？|%s으로
할까?
You don't have\nenough coins.|コインが
たりません|동전이
부족해
Oh. Please come\nback with coins!|コインを もって
また おこしください！|동전을 가지고
다시 와 주세요!
Oh? You don't have\na COIN CASE.|あれ？ コインケースを
もっていませんね|어? 동전 케이스가
없군요
%s.\nIs that right?|%sで
いいですか？|%s으로
할까?
Sorry! You need\nmore coins.|すみません！
コインが たりません|미안합니다!
동전이 부족해요
Sorry. You can't\ncarry any more.|すみません
これいじょう もてません|미안합니다
더는 지닐 수 없어요
Do you need some\ngame coins?|ゲームの コインは
いかがですか？|게임 동전이
필요하세요?
You don't have\nenough money.|おかねが
たりません|돈이
부족해요
    lined up!|    そろった！|    나란히!
Won %d coins!|コイン%dまい あたり！|동전 %d개 당첨!
POKéMON\ndatabase|ポケモンの
じょうほう|포켓몬
정보
Party <PK><MN>\nstatus|てもちの ポケモンの
ようす|데리고 있는
포켓몬의 상태
Contains\nitems|どうぐが
はいっている|도구가
들어 있다
<PO><KE>GEAR|ポケギア|포켓기어
Trainer's\nkey device|トレーナーの
べんりな どうぐ|트레이너의
편리한 장치
Your own\nstatus|じぶんの
じょうほう|자신의
정보
Save your\nprogress|ここまでの ぼうけんを
レポートに かく|지금까지의
모험을 저장
Change\nsettings|せっていを
かえる|설정을
바꾼다
Installed\nadd-ons|ついかした
きのう|설치된
추가 기능
Return to\nthe title|タイトルがめんに
もどる|타이틀 화면으로
돌아간다
Quit and\nbe judged.|やめて
しんさを うける|그만두고
심사를 받는다
Return to the\ntitle screen?|タイトルがめんに
もどりますか？|타이틀 화면으로
돌아갈까?
Saving… Leave ON!|レポートを かいています
でんげんを きらないで！|저장하고 있습니다
전원을 끄지 마세요!
What level do you\nwant to challenge?|どの レベルに
ちょうせんしますか？|어느 레벨에
도전할까?
A party POKéMON\ntops this level.|その レベルを こえた
ポケモンが います|그 레벨을 넘는
포켓몬이 있어
Cancel your BATTLE\nROOM challenge?|バトルルームの ちょうせんを
やめますか？|배틀룸 도전을
그만둘까?
Are you a boy?\nOr are you a girl?|おとこのこですか？
それとも おんなのこですか？|남자아이니?
아니면 여자아이니?
What?|なに？|뭐라고?
%s?|%s？|%s?
Whoa!|なんと！|아니!
%d min.?|%dふん じゃと？|%d분이라고?
%s, is that right?|%sで いいですか？|%s 맞니?
%s o'clock|%sじ|%s시
%d min.|%dふん|%d분
%s!\nIt's so dark!|%s！
まっくら じゃないか！|%s!
아주 어둡구나!
%s!\nI overslept!|%s！
ねすごしたようじゃ！|%s!
늦잠을 잤구나!
%s!\nYikes! I over-\nslept!|%s！
しまった！ ねすごした！|%s!
이런! 늦잠을 잤구나!
Coins:\n%d|コイン:
%dまい|동전:
%d개
You now have\n%d points.|いまの ポイントは
%dてんです|현재 포인트는
%d점입니다
%s DST,\nis that OK?|%s サマータイムで
よろしいですか？|%s 서머 타임으로
맞니?
%s,\nis that OK?|%sで
よろしいですか？|%s으로
맞니?
%s is\nnot compatible\vwith %s.|%sと
%sは あいしょうが わるい|%s와(과)
%s은(는) 맞지 않아
%s knows\n%s.|%sは
%sを おぼえている|%s은(는)
%s을(를) 알고 있어
This certifies\nthat you have\ncompleted the\nnew #DEX.\nCongratulations!|あたらしい ポケモンずかんを
みごとに かんせいさせた
ことを ここに しょうめいします
おめでとう！|새로운 포켓몬 도감을
훌륭하게 완성한 것을
여기에 증명합니다
축하합니다!
<PK><MN> are listed by|ポケモンを ならべる|포켓몬을 나열하는
evolution type.|しんかの じゅんばん|진화 순서
official type.|ずかんばんごう じゅん|도감 번호 순서
<PK><MN> are listed|ポケモンを ならべる|포켓몬을 나열합니다
alphabetically.|ABCの じゅんばん|ABC 순서로
UNOWN are listed|アンノーンを ならべる|안농을 나열합니다
in catching order.|つかまえた じゅんばん|잡은 순서로
Today's %s,|きょうは %s|오늘은 %s
Number is %05d!|ばんごうは %05d！|번호는 %05d!
    lined up!\nWon %d coins!|    そろった！\nコイン%dまい あたり！|    나란히!\n동전 %d개 당첨!
What?\n%s?|なに？\n%sじゃと？|뭐라고?\n%s라고?
Whoa!\n%d min.?|なんと！\n%dふん じゃと？|아니!\n%d분이라고?
This certifies|あなたが|당신이
that you have|あたらしい ポケモンずかんを|새로운 포켓몬 도감을
completed the|かんせい させたことを|완성했다는 것을
new #DEX.|ここに しょうめいします|여기에 증명합니다
Congratulations!|おめでとう！|축하합니다!
'''
# Left column has escaped line controls because each record is one line.
# Translation continuations above are actual line breaks; group at the next |.
def entries():
    current=[]
    for line in ROWS.splitlines():
        if line.count('|')>=1 and current and ''.join(current).count('|')==2:
            yield '\n'.join(current).split('|');current=[]
        current.append(line)
    if current:yield '\n'.join(current).split('|')
def unescape(s):
    return s.replace('\\\\','\\').replace('\\n','\n').replace('\\f','\f').replace('\\v','\v')
def translations(language,keys):
    out={}
    for row in entries():
        assert len(row)==3,row
        source=unescape(row[0]);value=unescape(row[1 if language=='ja'else 2])
        if source in keys:
            if language=='ko':value=value.translate(str.maketrans('１２３４５','12345'))
            out[source]={'value':value}
    return out

def harvest(engine):
    # The port credit roll prints its own labels without Strings.source.
    # Include only those actual literals, retaining all author/project names.
    from gen2_engine_strings import harvest as base, QUOTED, literal
    result=base(engine);path=engine/'src/ui/gen2/Credits.lua'
    for match in QUOTED.finditer(path.read_text()):
        value=literal(match[0])
        if value not in result:result[value]=[str(path.relative_to(engine))]
    return result
