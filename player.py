from ecc.curves import get_curve
from ecc.elliptic import inv
import socket
from os import urandom
import hashlib

"""
目前的问题：
1. 由于python与c++的性能差异， 要不要用python来实现线上部分
2. socket如何传输长数据以及列表
3. 有限域上点的运算
"""


class Player():
    num_player = 0
    bits = None
    cn = None
    n = None
    cp = None
    cq = None
    g = None

    def __init__(self,start_port, ip='localhost', bits=256, max_position=10000):
        self.no = Player.num_player
        Player.num_player += 1
        self.ip = ip
        self.position = 0
        self.max_position = max_position
        self.start_port = start_port
        self.rec_port = self.start_port
        if not Player.bits:
            try:
                Player.bits, Player.cn, Player.n, Player.cp, Player.cq, Player.g = get_curve(bits)
            except KeyError:
                raise ValueError

    def send_num(self,number, target_ip, target_port):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((target_ip, target_port))
        s.send(str(number).encode())
        s.close()

    def prep_rec(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("", self.rec_port))
        #print(self.rec_port)
        s.listen(1)
        self.conn, self.addr = s.accept()
        self.soc=s
        data = self.conn.recv(1024).decode()
        self.conn.close()
        self.position = (self.position+1)% self.max_position
        self.rec_port = self.start_port + self.position
        self.other = eval(data)

    def randkey(self, bits, n):
        '''Generate a random number (mod n) having the specified bit length'''
        rb = urandom(bits // 8 + 8)  # + 64 bits as recommended in FIPS 186-3
        c = 0
        for r in rb:
            c = (c << 8) | r
            # c = (c << 8) | ord(r)
        return (c % (n - 1)) + 1


class InputPlayer(Player):
    def __init__(self,rec_port, ip='localhosy'):
        super().__init__(rec_port, ip)

    def set_message(self, message, hash_name='sha256'):
        hash_func = hashlib.new(hash_name, message.encode("utf-8"))
        hash_value = int(hash_func.hexdigest(), 16)
        for p in ComputePlayer.ComputeList:
            p.set_hash(hash_value)


class ComputePlayer(Player):
    ComputeNum = 0
    ComputeList = []

    def __init__(self, rec_port, ip='localhost'):
        super().__init__(rec_port, ip)
        ComputePlayer.ComputeList.append(self)
        ComputePlayer.ComputeNum += 1
        self.list_send = []
        self.list_product = []
        self.list_triple = []
        '''
        self.alpha = None
        self.broadcast = None
        self.private_key = None
        self.public_key = None
        self.k = None
        self.k_inv = []
        self.s = []
        self.gamma = None
        self.sigma = None
        self.delta = None
        self.hash_message = None
        self.share_values = []
        self.beaver_triples = []
        '''

    def set_hash(self, value):
        self.hash_message = value

    def set_mac(self, mac_num):
        self.alpha = mac_num

    def set_shares(self, shares):
        self.share_values = shares

    def set_beaver_triples(self, triples):
        self.beaver_triples = triples

    def set_broadcast(self, value):
        self.broadcast = value

    def beaver_multiply_local(self, multiply_x_mask, multiply_y_mask, triple):
        a, b, c = triple
        n = Player.n
        temp1 = (a[0] * multiply_y_mask + b[0] * multiply_x_mask + c[0] + multiply_y_mask * multiply_x_mask) % n
        temp2 = (a[1] * multiply_y_mask + b[1] * multiply_x_mask + c[1] + multiply_y_mask * multiply_x_mask*self.alpha) % n
        self.product = (temp1, temp2)
        return self.product

    def set_multiply_x(self, value):
        self.multiply_x = value

    def set_multiply_y(self, value):
        self.multiply_y = value


class TrustedThirdParty(Player):
    def __init__(self, rec_port, ip='localhost'):
        super().__init__(rec_port, ip)
        self.mac_sum = 0

    def calculate_share(self, inputs):
        shares = [[] for _ in range(ComputePlayer.ComputeNum)]
        for i in inputs:
            sum = 0
            for j in range(ComputePlayer.ComputeNum - 1):
                temp = self.randkey(Player.bits, Player.n)
                shares[j].append(temp)
                sum = (sum + temp) % Player.n
            shares[ComputePlayer.ComputeNum-1].append((i - sum) % Player.n)
        return shares

    def generate_mac(self):
        self.mac_sum = self.randkey(Player.bits, Player.n)
        shares = self.calculate_share([self.mac_sum])
        for i in range(ComputePlayer.ComputeNum):
            ComputePlayer.ComputeList[i].set_mac(shares[i][0])

    def generate_mac_share(self, number):
        all_shares = [[] for _ in range(ComputePlayer.ComputeNum)]
        for i in range(number):
            num = self.randkey(Player.bits, Player.n)
            mac_num = (num * self.mac_sum) % Player.n
            temp = (num, mac_num)
            shares = self.calculate_share(temp)

            for j in range(ComputePlayer.ComputeNum):
                all_shares[j].append(tuple(shares[j]))
        for i in range(ComputePlayer.ComputeNum):
            ComputePlayer.ComputeList[i].set_shares(all_shares[i])

    def generate_beaver_triples(self, number):
        n = Player.n
        all_shares = [[] for _ in range(ComputePlayer.ComputeNum)]
        for i in range(number):
            a = self.randkey(Player.bits, Player.n)
            b = self.randkey(Player.bits, Player.n)
            c = (a * b) % n
            temp = (a, b, c, (a * self.mac_sum)%n, (b*self.mac_sum)%n, (c*self.mac_sum)%n)
            shares = self.calculate_share(temp)

            for j in range(ComputePlayer.ComputeNum):
                beaver_mac = tuple((shares[j][k], shares[j][k+3]) for k in range(3))
                all_shares[j].append(beaver_mac)
                #all_shares[j].append(tuple(shares[j][:3]))
        for i in range(ComputePlayer.ComputeNum):
            ComputePlayer.ComputeList[i].set_beaver_triples(all_shares[i])


if __name__ == '__main__':
    a = InputPlayer(10000)
    b = TrustedThirdParty(20000)
    c = ComputePlayer(30000)
    d = ComputePlayer(40000)

    a.set_message("hello world")
    b.generate_mac()
    b.generate_mac_share(100)
    b.generate_beaver_triples(100)
    print(c.alpha, c.hash_message,c.beaver_triples)
    print(d.alpha, d.hash_message,d.share_values)
    print(b.mac_sum, inv(b.mac_sum, Player.n))
