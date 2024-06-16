# includes
import clr
import ctypes

clr.AddReference('System.IO')
clr.AddReference('System.Drawing')
clr.AddReference('System.Reflection')
clr.AddReference('System.Threading')
clr.AddReference('System.Windows.Forms')

import System.IO
import System.Drawing
import System.Reflection
import System.Threading
import System.Windows.Forms

from System.Threading import ApartmentState, Thread, ThreadStart
# !includes

num_of_disks = 3  # inicijalni broj diskova
disk_placement = [  # lista stubova
    [],[],[]
]

disk_colors = [  # boje diskova
    System.Drawing.Color.FromArgb(45, 48, 71),
    System.Drawing.Color.FromArgb(147, 183, 190),
    System.Drawing.Color.FromArgb(224, 202, 60),
    System.Drawing.Color.FromArgb(178, 255, 214),
    System.Drawing.Color.FromArgb(167, 153, 183),
    System.Drawing.Color.FromArgb(4, 138, 129)
]


pillar_x = [150, 350, 550]  # pozicija prvog, drugog i treceg stuba

first_disk_y = 490  # y koordinata gde ce se najnizi prsten pojaviti
smallest_disk_width = 60  # koliko je najmanji disk sirok (+10 za svaki naredni)
disk_height = 30  # visina/debljina diska

taking = False  # flag koji nam govori u kojem smo statusu, da li smo uzeli disk ili treba da uzmemo disk
selected_pillar = -1  # izabrani stub sa kojeg uzimamo disk

lives = 3  # pocetni broj zivota

#  funkcija koja nam stampa broj zivota kao string srca
def get_lives_str():
    global lives
    lives_str = ""
    for i in range(lives):
        lives_str = lives_str + "❤ "
    return lives_str


#  forma na kojoj je sama igrica
class GameWindow(System.Windows.Forms.Form):
    def __init__(self):
        self.clr_black = System.Drawing.Color.FromArgb(0, 0, 0)  # crna boja

        # info o samoj formi
        self.Text = "Hanojske kule"
        self.BackColor = System.Drawing.Color.FromArgb(238, 238, 238)
        self.ClientSize = System.Drawing.Size(800, 600)
        self.MinimumSize = System.Drawing.Size(800, 600)
        self.MaximumSize = System.Drawing.Size(800, 600)

        # kontrole na formi
        self.pillarButtons = []
        self.pillarButtons.append(System.Windows.Forms.Button())
        self.pillarButtons.append(System.Windows.Forms.Button())
        self.pillarButtons.append(System.Windows.Forms.Button())

        # dugme ispod prvog stuba
        self.pillarButtons[0].Location = System.Drawing.Point(pillar_x[0] - 25 + 5, 490) 
        self.pillarButtons[0].Size = System.Drawing.Size(50, 50)
        self.pillarButtons[0].Click += self.pillarOneButton_Click
        self.pillarButtons[0].Text = "UZMI"
        self.Controls.Add(self.pillarButtons[0])

        # dugme ispod drugog stuba
        self.pillarButtons[1].Location = System.Drawing.Point(pillar_x[1] - 25 + 5, 490)
        self.pillarButtons[1].Size = System.Drawing.Size(50, 50)
        self.pillarButtons[1].Click += self.pillarTwoButton_Click
        self.pillarButtons[1].Text = "UZMI"
        self.Controls.Add(self.pillarButtons[1])

        # dugme ispod treceg stuba
        self.pillarButtons[2].Location = System.Drawing.Point(pillar_x[2] - 25 + 5, 490)
        self.pillarButtons[2].Size = System.Drawing.Size(50, 50)
        self.pillarButtons[2].Click += self.pillarThreeButton_Click
        self.pillarButtons[2].Text = "UZMI"
        self.Controls.Add(self.pillarButtons[2])

        # reload igre i broj diskova za narednu igru
        self.lblNumberOfDisks = System.Windows.Forms.Label()
        self.lblNumberOfDisks.Location = System.Drawing.Point(50, 20)
        self.lblNumberOfDisks.Size = System.Drawing.Size(100, 30)
        self.lblNumberOfDisks.Text = "Unesi broj diskova(od 3 - 8):"
        self.Controls.Add(self.lblNumberOfDisks)

        self.txtNumberOfDisks = System.Windows.Forms.TextBox()
        self.txtNumberOfDisks.Location = System.Drawing.Point(50, 50)
        self.txtNumberOfDisks.Size = System.Drawing.Size(100, 20)
        self.txtNumberOfDisks.Text = "3"
        self.Controls.Add(self.txtNumberOfDisks)

        self.btnReloadGame = System.Windows.Forms.Button()
        self.btnReloadGame.Location = System.Drawing.Point(160, 20)
        self.btnReloadGame.Size = System.Drawing.Size(51, 51)
        self.btnReloadGame.Text = "Reload"
        self.btnReloadGame.Click += self.btnReloadGame_Click
        self.Controls.Add(self.btnReloadGame)

        # label za zivote
        self.lblLives = System.Windows.Forms.Label()
        self.lblLives.Location = System.Drawing.Point(600, 20)
        self.lblLives.Size = System.Drawing.Size(200, 100)
        self.lblLives.Text = get_lives_str()
        self.lblLives.BackColor = System.Drawing.Color.White
        self.lblLives.Font = System.Drawing.Font("Arial", 20.0)
        self.lblLives.ForeColor = System.Drawing.Color.Red
        self.Controls.Add(self.lblLives)

        # picturebox koji ce da drzi grafiku koju nacrtamo, mora da stoji na kraju!
        self.pictureBox = System.Windows.Forms.PictureBox()
        self.pictureBox.Dock = 5  # fill
        self.Controls.Add(self.pictureBox)

        self.bitmap = System.Drawing.Bitmap(self.pictureBox.Width, self.pictureBox.Height)
        self.pictureBox.Image = self.bitmap
        
        self.draw_game()  # funkcija koja crta stanje igre

    # funkcija kojom uzimamo disk sa stuba, postavlja taking na true i selected_pillar na stub s kojeg uzimamo disk
    def take_disk(self, from_pillar):  
        if len(disk_placement[from_pillar]) > 0:
            global taking, selected_pillar
            taking = True
            selected_pillar = from_pillar

            for i in range(3):
                self.pillarButtons[i].Text = "STAVI"

    # funkcija koja spusta disk na odredjeni stub, prvo proverava da li je igra u stanju spustanja stuba (odnosno da smo vec uzeli disk, taking = True)            
    # nakon toga ukoliko se stub s kojeg smo uzeli disk i stub na koji stavljamo disk razlikuju radimo potrebne provere za premestanje diska (ako spustamo na isti stub s kojeg smo uzeli ne desava se nista)
    def drop_disk(self, to_pillar):
        global taking, selected_pillar
        if taking:
            taking = False
            for i in range(3):
                self.pillarButtons[i].Text = "UZMI"
            if selected_pillar != to_pillar:
                if len(disk_placement[to_pillar]) > 0:  # provere za velicinu diska radimo samo ako stub na koji spustamo disk nije prazan
                    disk_size = disk_placement[selected_pillar][len(disk_placement[selected_pillar]) - 1]  # uzimamo velicinu diska koji smo podigli
                    dest_disk_size = disk_placement[to_pillar][len(disk_placement[to_pillar]) - 1]  # uzimamo velicinu diska na vrhu stuba na koji spustamo disk

                    global lives
                    if dest_disk_size < disk_size:  # nije dozvoljeno da disk na vrhu stuba na koji spustamo bude manji od diska koji zelimo da spustimo
                        lives = lives - 1  # ako pogresimo gubimo zivot
                        ctypes.windll.user32.MessageBoxW(0, "Pogresan potez! Ne mozete staviti veci disk preko manjeg", "Greska", 0)
                        if lives == 0:  # kada izgubimo sve zivote, poraz, vracamo se na pocetak
                            ctypes.windll.user32.MessageBoxW(0, "Izgubili ste, pokusajte ponovo!", "Game Over", 0)
                            lives = 3
                            global num_of_disks
                            num_of_disks = int(self.txtNumberOfDisks.Text)
                            reload_game(num_of_disks)
                            self.draw_game()
                            self.pictureBox.Refresh()

                        self.lblLives.Text = get_lives_str()
                        return

                # uzimamo disk i premestamo ga na drugi stub
                disk = disk_placement[selected_pillar][len(disk_placement[selected_pillar]) - 1]
                disk_placement[selected_pillar].pop()  # izbacujemo ga sa vrha stuba na kojem je bio do sad
                disk_placement[to_pillar].append(disk)  # stavljamo ga na novi stub
                self.draw_game()  # ponovo crtamo igru
                self.pictureBox.Refresh()  # refresh je obavezan da bi se stanje promenilo

                # proveravamo da li je bilo koji stub sem prvog popunjen do vrha (svi diskovi na njemu), ako jeste kraj igre, pobeda
                if len(disk_placement[1]) == num_of_disks or len(disk_placement[2]) == num_of_disks:
                    ctypes.windll.user32.MessageBoxW(0, "Pobedili ste, cestitamo!", "Pobeda", 0)
                    self.pillarButtons[0].Enabled = False
                    self.pillarButtons[1].Enabled = False
                    self.pillarButtons[2].Enabled = False

    # click dugmeta za reload, resetuje igru sa brojem diskova iz textboxa (minimum 3, max nije postavljen)
    def btnReloadGame_Click(self, sender, args):
        global num_of_disks, lives
        lives = 3
        num_of_disks = int(self.txtNumberOfDisks.Text)
        
        num_of_disks = min(num_of_disks, 8) #maksimalan broj diskova je 8

        if num_of_disks < 3:
            ctypes.windll.user32.MessageBoxW(0, "Minimum diskova je 3!", "Greska", 0)
            self.txtNumberOfDisks.Text = "3"
            num_of_disks = int(self.txtNumberOfDisks.Text)
        elif num_of_disks > 8:
            ctypes.windll.user32.MessageBoxW(0, "Maksimum diskova je 8!", "Greska", 0)
            self.txtNumberOfDisks.Text = "8"
            num_of_disks = 8
        
        reload_game(num_of_disks)
        self.draw_game()
        self.pictureBox.Refresh()

        self.pillarButtons[0].Enabled = True
        self.pillarButtons[1].Enabled = True
        self.pillarButtons[2].Enabled = True

    def pillarOneButton_Click(self, sender, args):
        if not taking:
            self.take_disk(0)
        else:
            self.drop_disk(0)

    def pillarTwoButton_Click(self, sender, args):
        if not taking:
            self.take_disk(1)
        else:
            self.drop_disk(1)

    def pillarThreeButton_Click(self, sender, args):
        if not taking:
            self.take_disk(2)
        else:
            self.drop_disk(2)

    # crtanje diskova
    def draw_disks(self, graph):
        pillar_count = 0
        for pillar in disk_placement:  # svaki stub pojedinacno
            level = 0  # level 0 je najniza pozicija za disk
            for disk in pillar:
                brush = System.Drawing.SolidBrush(disk_colors[disk % len(disk_colors)])  # uzimamo boju iz liste gore, mod sa brojem boja tako da ako ima vise diskova nego boja krenuce da se ponavljaju boje
                graph.FillRectangle(brush, 
                                    round(pillar_x[pillar_count] - ((smallest_disk_width + disk * 10)/2) + 5), # x = pozicija pillara - polovina sirine diska + 5 (polovina sirine pillara)
                                    450 - disk_height - disk_height * level,  # y = 450 (pozicija donje linije koja drzi stubove) - visina diska - visina svakog narednog diska
                                    (smallest_disk_width + disk * 10), # sirina diska
                                    disk_height) # visina diska
                level = level + 1  # kada nacrtamo disk prelazimo na sledeci level (sledeci disk ide iznad postavljenog)
            pillar_count = pillar_count + 1

    def draw_game(self):
        graphics = System.Drawing.Graphics.FromImage(self.bitmap)
        graphics.Clear(System.Drawing.Color.White)
        brush = System.Drawing.SolidBrush(System.Drawing.Color.Black)

        graphics.FillRectangle(brush, 50, 450, 650, 10)  # donja linija koja drzi stubove
        graphics.FillRectangle(brush, pillar_x[0], 150, 10, 300)  # stub 1
        graphics.FillRectangle(brush, pillar_x[1], 150, 10, 300)  # stub 2
        graphics.FillRectangle(brush, pillar_x[2], 150, 10, 300)  # stub 3

        self.draw_disks(graphics)

        graphics.Dispose()

    def run(self):
        System.Windows.Forms.Application.Run(self)


def game_thread():  # thread u kojem pravimo instancu klase prozora igre
    game_form = GameWindow()
    win_form_app = System.Windows.Forms.Application
    win_form_app.Run(game_form)  # pokrecemo igru


def reload_game(disk_num):  # restart igre
    disk_placement[0].clear()
    disk_placement[1].clear()
    disk_placement[2].clear()
    for i in range(disk_num-1,-1,-1):
        disk_placement[0].append(i)


if __name__ == "__main__":  # main
    reload_game(num_of_disks)
    game_thread()
