"""Original vector character art and page drawing helpers."""
from contextlib import contextmanager
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

INK = '#273F48'
CREAM = '#FFF9EB'
PAPER = '#FFFCF5'
TEAL = '#397F7B'
MINT = '#DCEEDC'
SKY = '#DBF0F3'
RED = '#ED6063'
YELLOW = '#F6CD69'
PEACH = '#FFE4CC'
MUTED = '#577079'

FONTDIR = '/System/Library/Fonts/Supplemental/'
pdfmetrics.registerFont(TTFont('Round', FONTDIR + 'Arial Rounded Bold.ttf'))
pdfmetrics.registerFont(TTFont('Body', FONTDIR + 'Trebuchet MS.ttf'))
pdfmetrics.registerFont(TTFont('BodyBold', FONTDIR + 'Trebuchet MS Bold.ttf'))


class Art:
    def __init__(self, canvas):
        self.c = canvas
        self.text_boxes = []

    @contextmanager
    def at(self, x=0, y=0, scale=1):
        self.c.saveState()
        self.c.translate(x, y)
        self.c.scale(scale, scale)
        yield
        self.c.restoreState()

    def style(self, fill, stroke, sw=2):
        if fill:
            self.c.setFillColor(HexColor(fill))
        if stroke:
            self.c.setStrokeColor(HexColor(stroke))
        self.c.setLineWidth(sw)
        self.c.setLineCap(1)
        self.c.setLineJoin(1)

    def rect(self, x, y, w, h, fill, stroke=None, r=0, sw=2):
        self.style(fill, stroke, sw)
        if r:
            self.c.roundRect(x, y, w, h, r, stroke=bool(stroke), fill=bool(fill))
        else:
            self.c.rect(x, y, w, h, stroke=bool(stroke), fill=bool(fill))

    def oval(self, x, y, w, h, fill, stroke=None, sw=2):
        self.style(fill, stroke, sw)
        self.c.ellipse(x, y, x+w, y+h, stroke=bool(stroke), fill=bool(fill))

    def line(self, x1, y1, x2, y2, stroke=INK, sw=2):
        self.style(None, stroke, sw)
        self.c.line(x1, y1, x2, y2)

    def path(self, data, fill=None, stroke=INK, sw=2, close=False):
        self.style(fill, stroke, sw)
        p = self.c.beginPath()
        for op in data:
            if op[0] == 'M': p.moveTo(*op[1:])
            elif op[0] == 'L': p.lineTo(*op[1:])
            elif op[0] == 'C': p.curveTo(*op[1:])
            elif op[0] == 'Z': p.close()
        if close: p.close()
        self.c.drawPath(p, stroke=bool(stroke), fill=bool(fill))

    def text(self, text, x, y, size=18, font='Body', color=INK, align='left'):
        self.c.saveState()
        self.c.translate(x, y)
        self.c.scale(1, -1)
        self.c.setFillColor(HexColor(color))
        self.c.setFont(font, size)
        width = pdfmetrics.stringWidth(text, font, size)
        dx = 0 if align == 'left' else (-width/2 if align == 'center' else -width)
        self.c.drawString(dx, -size*0.83, text)
        self.c.restoreState()
        return width

    def lines(self, lines, x, y, size=18, leading=None, **kw):
        leading = leading or size*1.28
        for i, line in enumerate(lines): self.text(line, x, y+i*leading, size, **kw)

    def wrap(self, text, x, y, width, size=15, leading=None, font='Body', color=INK):
        lines = []
        current = ''
        for word in text.split():
            test = current + (' ' if current else '') + word
            if pdfmetrics.stringWidth(test, font, size) > width:
                if current: lines.append(current)
                current = word
            else: current = test
        if current: lines.append(current)
        self.lines(lines, x, y, size, leading, font=font, color=color)
        return len(lines)*(leading or size*1.28)

    def bubble(self, x, y, w, h, words, tail, size=19):
        """A clear speech balloon with a tail that points to the speaker."""
        tx, ty = tail
        base = max(x+18, min(x+w-18, tx))
        self.path([('M',base-10,y+h-5),('L',tx,ty),('L',base+10,y+h-5)], '#FFFFFF', INK, 1.7, True)
        self.rect(x,y,w,h,'#FFFFFF',INK,r=15,sw=1.7)
        self.line(base-8,y+h-1,base+8,y+h-1,'#FFFFFF',3)
        lines = words if isinstance(words, list) else [words]
        yy = y + (h-len(lines)*size*1.2)/2
        self.lines(lines,x+w/2,yy,size,leading=size*1.2,font='Round',align='center')

    def grass(self, x, y, s=1):
        with self.at(x,y,s):
            self.path([('M',0,0),('C',-2,-5,-4,-7,-7,-9)],stroke='#72A983',sw=1.8)
            self.line(0,0,2,-12,'#72A983',1.8)
            self.path([('M',0,0),('C',3,-4,6,-6,9,-6)],stroke='#72A983',sw=1.8)

    def flower(self, x,y,s=1):
        with self.at(x,y,s):
            self.line(0,0,0,15,'#609176',2)
            for dx,dy in [(-5,0),(5,0),(0,-5),(0,5)]: self.oval(dx-4,dy-4,8,8,CREAM)
            self.oval(-3,-3,6,6,YELLOW)

    def sparkle(self,x,y,s=1,color=YELLOW):
        with self.at(x,y,s):
            self.path([('M',0,-10),('C',2,-3,3,-2,10,0),('C',3,2,2,3,0,10),('C',-2,3,-3,2,-10,0),('C',-3,-2,-2,-3,0,-10)],color,None,close=True)

    def cloud(self,x,y,s=1):
        with self.at(x,y,s):
            self.path([('M',0,25),('C',-5,11,11,5,21,12),('C',21,-7,47,-6,49,12),('C',65,0,80,12,76,24),('C',87,34,66,39,53,35),('L',13,35),('C',5,36,-3,32,0,25)],'#FFFFFF',None,close=True)

    def sun(self,x,y,r=24):
        import math
        for i in range(10):
            angle=i*math.pi/5
            self.line(x+math.cos(angle)*(r+7),y+math.sin(angle)*(r+7),x+math.cos(angle)*(r+12),y+math.sin(angle)*(r+12),YELLOW,2.3)
        self.oval(x-r,y-r,2*r,2*r,'#F8D77E')

    def park(self,w=540,h=196,variant=0):
        self.rect(0,0,w,h,SKY)
        self.cloud(365,20,.65)
        self.cloud(54,34,.42)
        self.path([('M',0,h*.64),('C',w*.23,h*.39,w*.37,h*.83,w*.63,h*.63),('C',w*.82,h*.43,w*.9,h*.6,w,h*.56),('L',w,h),('L',0,h)],'#BFDABD',None,close=True)
        self.path([('M',0,h*.81),('C',w*.32,h*.63,w*.56,h*.92,w,h*.72),('L',w,h),('L',0,h)],'#DCECCB',None,close=True)
        self.path([('M',-10,h-15),('C',w*.31,h-60,w*.62,h+4,w+20,h-40)],stroke='#F6E9C7',sw=24)
        for x,y in [(30,h-12),(248,h-23),(466,h-7),(503,h-34)]: self.grass(x,y,.55)
        self.flower(496,h-50,.55)
        self.flower(22,h-42,.45)

    def ball(self,x,y,s=1):
        with self.at(x,y,s):
            self.oval(0,0,60,60,RED,INK,2.4)
            self.path([('M',12,6),('C',8,24,27,47,48,51)],stroke='#B7414D',sw=1.9)
            self.path([('M',25,5),('C',45,11,53,26,53,37)],stroke='#FFD5C7',sw=6)
            self.oval(11,13,9,6,'#FFE6D7')

    def rabbit(self,x,y,s=1,pose='stand',mood='happy',facing='right'):
        with self.at(x,y,s):
            if facing=='left':
                self.c.translate(135,0);self.c.scale(-1,1)
            self.oval(21,196,112,13,'#B3C7AC')
            self.oval(18,148,28,29,'#FFF9EC',INK,2.3)
            # Long ears create a consistent silhouette in every panel.
            self.path([('M',41,73),('C',24,46,20,5,35,3),('C',53,0,62,49,59,73)],'#FFF9EC',INK,2.6,True)
            self.path([('M',43,54),('C',34,31,32,11,38,11),('C',46,13,50,39,51,55)],'#F4C4B9',None,close=True)
            self.path([('M',68,69),('C',61,35,72,0,87,8),('C',100,15,93,48,85,76)],'#FFF9EC',INK,2.6,True)
            self.path([('M',76,55),('C',73,32,79,13,85,17),('C',91,22,85,44,82,56)],'#F4C4B9',None,close=True)
            # Legs and feet.
            if pose=='kick':
                self.path([('M',77,175),('C',97,174,119,162,130,167),('C',148,168,154,181,144,188),('C',127,193,109,183,87,195)],'#FFF9EC',INK,2.5,True)
                self.oval(36,182,37,21,'#FFF9EC',INK,2.5)
            else:
                self.oval(40,182,34,21,'#FFF9EC',INK,2.5)
                self.oval(81,184,41,20,'#FFF9EC',INK,2.5)
            self.path([('M',46,114),('C',25,125,34,176,48,187),('C',65,199,94,195,104,180),('C',113,157,111,128,94,116)],'#6CA8A4',INK,2.6,True)
            self.rect(61,150,27,20,'#93C2B4',INK,r=6,sw=1.7)
            self.line(49,123,54,142,'#D4E7C6',6)
            self.line(94,123,91,142,'#D4E7C6',6)
            self.oval(51,139,5,5,YELLOW)
            self.oval(89,139,5,5,YELLOW)
            # Arms.
            if pose=='wave':
                self.path([('M',99,127),('C',119,125,122,106,119,94),('C',120,84,131,85,134,94),('C',143,121,127,143,111,150)],'#FFF9EC',INK,2.5,True)
            elif pose=='point':
                self.path([('M',100,129),('C',116,136,129,130,139,127),('C',152,124,157,136,146,142),('C',129,153,113,154,105,150)],'#FFF9EC',INK,2.5,True)
            elif pose=='hold':
                self.path([('M',104,127),('C',121,133,118,152,111,159),('C',98,168,89,155,94,149)],'#FFF9EC',INK,2.5,True)
            else:
                self.path([('M',102,127),('C',119,143,120,155,113,163),('C',106,170,98,162,100,153)],'#FFF9EC',INK,2.5,True)
            self.path([('M',42,131),('C',27,141,26,161,36,168),('C',45,174,53,164,48,156)],'#FFF9EC',INK,2.5,True)
            # Face and soft muzzle.
            self.path([('M',23,86),('C',19,61,39,49,66,51),('C',92,50,113,61,112,81),('C',127,87,130,104,118,116),('C',104,129,76,131,51,120),('C',31,115,23,103,23,86)],'#FFF9EC',INK,2.6,True)
            self.oval(80,94,42,27,'#F4E9D4')
            self.oval(49,94,17,10,'#F1BCAF')
            if mood=='happy':
                self.oval(59,79,6,9,INK)
                self.oval(91,77,6,9,INK)
                self.path([('M',92,106),('C',97,112,105,111,109,105)],stroke=INK,sw=1.9)
            elif mood=='sad':
                self.oval(59,83,6,8,INK)
                self.oval(91,82,6,8,INK)
                self.line(54,76,65,72,INK,1.8)
                self.line(91,73,102,77,INK,1.8)
                self.path([('M',94,112),('C',97,105,106,105,111,110)],stroke=INK,sw=1.9)
            elif mood=='surprised':
                self.oval(59,78,7,10,INK)
                self.oval(91,76,7,10,INK)
                self.oval(99,105,7,10,INK)
            self.path([('M',109,94),('C',111,89,120,89,120,95),('C',119,100,113,101,109,94)],'#AE6C65',None,close=True)
            # Golden neckerchief.
            self.path([('M',43,120),('C',65,130,87,132,106,121),('L',102,135),('C',76,145,57,138,43,131)],YELLOW,INK,1.8,True)
            self.path([('M',51,132),('L',46,155),('L',61,148),('L',66,135)],YELLOW,INK,1.8,True)

    def bird(self,x,y,s=1,facing='left',flying=False):
        with self.at(x,y,s):
            if facing=='right':
                self.c.translate(100,0);self.c.scale(-1,1)
            if not flying: self.oval(15,81,70,8,'#B3C7AC')
            self.path([('M',67,53),('L',94,36),('L',91,59),('L',99,58),('L',84,73)],'#EDA757',INK,2.2,True)
            self.line(39,73,37,84,'#A66B45',2.5)
            self.line(58,73,61,84,'#A66B45',2.5)
            self.line(37,84,27,84,'#A66B45',2.5)
            self.line(61,84,52,84,'#A66B45',2.5)
            self.path([('M',10,33),('C',6,8,28,1,47,12),('C',63,17,69,33,77,46),('C',91,70,70,83,42,79),('C',12,78,7,58,10,33)],YELLOW,INK,2.4,True)
            self.path([('M',46,6),('C',39,2,36,1,35,3),('M',47,9),('C',46,2,50,0,52,2)],stroke=INK,sw=2)
            self.path([('M',12,34),('L',-3,41),('L',13,47)],'#DF8350',INK,2,True)
            self.oval(22,29,6,8,INK)
            self.oval(15,46,12,8,'#EAA181')
            if flying:
                self.path([('M',52,42),('C',65,21,81,7,89,13),('C',99,21,74,49,60,57)],'#6DAAA2',INK,2,True)
            else:
                self.path([('M',51,38),('C',70,37,83,58,74,65),('C',59,72,47,55,51,38)],'#6DAAA2',INK,2,True)
                self.path([('M',61,45),('C',68,53,69,56,70,58)],stroke='#3E7B76',sw=1.5)

    def tree(self,x,y,s=1):
        with self.at(x,y,s):
            self.oval(10,177,188,19,'#B3C7AC')
            self.path([('M',84,175),('L',88,84),('L',109,84),('L',119,174),('L',131,181),('C',113,191,84,188,70,181)],'#B98960',INK,2.8,True)
            self.path([('M',92,119),('L',69,98),('M',106,134),('L',130,107)],stroke=INK,sw=2.7)
            self.path([('M',43,121),('C',12,125,-3,92,14,72),('C',-3,51,23,23,45,30),('C',44,2,87,-5,102,14),('C',124,-4,155,12,154,30),('C',186,23,209,56,191,75),('C',213,107,190,127,161,124),('C',141,148,119,135,102,124),('C',80,144,56,136,43,121)],'#89B89A',INK,2.8,True)
            self.path([('M',33,81),('C',36,62,52,57,64,63),('M',121,42),('C',136,33,151,39,157,51),('M',147,105),('C',166,105,177,93,177,82)],stroke='#5F9A80',sw=3)
            for a,b in [(58,30),(123,93),(28,97)]: self.oval(a,b,8,5,'#BBD3A3')

    def leaf(self,x,y,s=1):
        with self.at(x,y,s):
            self.path([('M',2,60),('C',-11,29,3,8,24,4),('C',41,2,52,5,61,0),('C',60,21,63,49,41,62),('C',30,69,12,69,2,60)],'#E87862',INK,2.3,True)
            self.path([('M',-8,78),('C',5,57,22,30,48,12)],stroke='#864F4C',sw=2.3)
            self.path([('M',15,47),('L',10,30),('M',22,36),('L',40,38),('M',32,24),('L',31,13)],stroke='#864F4C',sw=1.5)

    def box(self,x,y,s=1,contents=None):
        with self.at(x,y,s):
            self.oval(-12,95,153,13,'#B3C7AC')
            self.path([('M',0,25),('L',38,7),('L',130,26),('L',92,52)],'#AB775A',INK,2.4,True)
            if contents=='hat': self.hat(23,-17,.72)
            if contents=='ball': self.ball(36,-6,.83)
            self.path([('M',0,28),('L',91,47),('L',90,104),('L',0,82)],'#D9A578',INK,2.4,True)
            self.path([('M',91,47),('L',130,27),('L',130,83),('L',90,104)],'#BD875F',INK,2.4,True)
            self.path([('M',0,28),('L',-16,12),('L',75,30),('L',91,47)],'#E9BE8F',INK,2.2,True)
            self.path([('M',91,47),('L',112,53),('L',148,32),('L',130,27)],'#E9BE8F',INK,2.2,True)
            self.path([('M',37,36),('L',53,39),('L',53,61),('L',46,56),('L',38,58)],'#FADEA9',None,close=True)

    def hat(self,x,y,s=1):
        with self.at(x,y,s):
            self.path([('M',17,48),('L',27,7),('C',40,-1,69,-1,80,7),('L',87,49)],RED,INK,2.3,True)
            self.path([('M',21,32),('C',41,38,65,38,83,33),('L',86,46),('C',67,54,36,52,19,45)],'#FFD1A3',INK,1.8,True)
            self.path([('M',17,44),('C',-7,43,-5,60,18,65),('C',51,73,97,70,105,58),('C',113,46,97,41,86,44),('C',73,52,34,53,17,44)],RED,INK,2.3,True)

    def bench(self,x,y,s=1,hidden_ball=False):
        with self.at(x,y,s):
            self.oval(-9,133,223,14,'#B3C7AC')
            if hidden_ball: self.ball(139,63,.83)
            for xx in [24,166]:
                self.rect(xx,30,10,107,'#637D74',INK,r=3,sw=2)
            self.rect(0,18,204,25,'#E1AA76',INK,r=5,sw=2.6)
            self.rect(0,49,204,25,'#E1AA76',INK,r=5,sw=2.6)
            self.path([('M',-7,86),('L',183,86),('L',213,103),('L',17,103)],'#E6B98C',INK,2.6,True)
            self.rect(17,103,196,9,'#B7815E',INK,r=2,sw=2)
            for xx in [22,170]:
                self.oval(xx,28,4,4,'#9C6D50')
                self.oval(xx,59,4,4,'#9C6D50')

    def scene(self,name,w=540,h=196):
        self.park(w,h)
        if name=='hello':
            self.sun(445,47,22)
            self.rabbit(141,10,.91,pose='wave')
            self.ball(278,130,.83)
            self.sparkle(344,121,.75)
            self.grass(389,169,.9)
        elif name=='friends':
            self.rabbit(97,h-184,.86,pose='wave')
            self.bird(340,h-106,1.05)
            self.ball(269,h-66,.83)
            self.bubble(24,10,214,47,'Hello, Pip!',(183,h-117),20)
            self.bubble(305,12,207,47,"Let's play!",(363,h-84),20)
        elif name=='kick':
            self.rabbit(87,12,.86,pose='kick')
            self.bird(369,91,.79)
            self.ball(300,70,.75)
            for xx,yy,ww in [(250,90,32),(256,106,34),(268,122,22)]: self.line(xx,yy,xx+ww,yy,'#A9AAA0',2.3)
            self.path([('M',295,153),('C',339,137,365,136,410,145)],stroke='#ACB8A0',sw=2)
        elif name=='gone':
            self.rabbit(82,26,.78,mood='surprised')
            self.bird(304,111,.79,facing='right')
            self.ball(515,125,.77)
            for xx,yy,ww in [(456,140,33),(466,155,30),(483,172,20)]: self.line(xx,yy,xx+ww,yy,'#A9AAA0',2.2)
            self.bubble(218,9,292,69,['Oh, no!','Where is my ball?'],(181,101),20)
        elif name=='tree_question':
            self.tree(315,-11,1.02)
            self.rabbit(78,35,.76,pose='point')
            self.bird(227,117,.66,facing='right')
            self.leaf(420,164,.18)
            self.bubble(30,9,297,44,'Is it under the tree?',(164,108),19)
        elif name=='leaf':
            self.tree(-38,-81,1.4)
            self.rabbit(351,24,.80,facing='left')
            self.bird(201,98,.91,facing='right')
            self.leaf(264,130,.58)
            self.bubble(200,8,242,49,'No. It is a leaf!',(245,119),20)
        elif name=='box_question':
            self.rabbit(65,31,.77,pose='point')
            self.bird(237,104,.76,facing='right')
            self.box(345,72,.98)
            self.bubble(32,7,270,46,'Is it in the box?',(150,100),20)
        elif name=='hat':
            self.box(320,71,1.03,contents='hat')
            self.bird(232,104,.83,facing='right')
            self.rabbit(62,24,.8)
            self.bubble(188,8,265,46,'No. It is a hat!',(267,123),20)
        elif name=='bench_question':
            self.bench(315,37,1,hidden_ball=True)
            self.rabbit(53,36,.76,pose='point')
            self.bird(224,73,.80,facing='right',flying=True)
            self.bubble(22,7,309,44,'Look behind the bench!',(257,95),18.5)
        elif name=='found':
            self.bench(5,48,.86)
            self.rabbit(258,32,.76,pose='wave')
            self.bird(419,111,.74)
            self.ball(365,131,.82)
            self.sparkle(427,119,.6)
            self.sparkle(387,99,.7)
            self.bubble(188,7,239,46,'My red ball!',(334,108),21)
        elif name=='thanks':
            self.rabbit(81,29,.78,pose='wave')
            self.bird(364,106,.87)
            self.ball(260,135,.78)
            self.bubble(27,7,247,44,'Thank you, Pip!',(165,107),19)
            self.bubble(295,9,220,44,"You're welcome!",(390,119),18.5)
        elif name=='play':
            self.sun(460,47,21)
            self.rabbit(95,28,.79,pose='kick')
            self.bird(369,91,.9,flying=True)
            self.ball(276,96,.79)
            self.bubble(214,7,197,44,"Let's play!",(186,106),21)
            self.sparkle(354,101,.6)
        else:
            raise ValueError(name)
