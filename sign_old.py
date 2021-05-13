from player import *
from threading import Thread
from elliptic import inv,mulp,add
import datetime
import time


def broadcast(players):
    #players = ComputePlayer.ComputeList
    #print(players[0].rec_port, players[1].rec_port)
    t1 = Thread(target=players[0].prep_rec, args=())
    t2 = Thread(target=players[1].send_num, args=(players[1].broadcast, players[0].ip, players[0].rec_port))
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    #print(players[0].rec_port, players[1].rec_port)
    t1 = Thread(target=players[1].prep_rec, args=())
    t2 = Thread(target=players[0].send_num, args=(players[0].broadcast, players[1].ip, players[1].rec_port))
    t1.start()
    t2.start()
    t1.join()
    t2.join()


def open_share_with_mac(players):
    n = Player.n
    for p in players:
        p.temp = p.broadcast
        p.set_broadcast(p.temp[0])
    broadcast(players)
    for p in players:
        p.open_value = (p.broadcast + p.other) % n
        p.set_broadcast((p.temp[1]-p.alpha * p.open_value) % n)
    broadcast(players)
    for p in players:
        p.mac_check = (p.broadcast + p.other) % n
        #print('open result', p.mac_check)


def open_point_with_mac(players):
    n, cp, cq, cn, g = Player.n, Player.cp, Player.cq, Player.cn, Player.g
    for p in players:
        p.temp = p.broadcast
        p.set_broadcast(p.temp[0])
    broadcast(players)
    for p in players:
        p.open_point = add(cp, cq, cn, p.broadcast, p.other)
        p.set_broadcast(mulp(cp,cq, cn, p.open_point, p.alpha))
    broadcast(players)
    for p in players:
        p.open_left = add(cp,cq,cn, p.broadcast, p.other)
        p.set_broadcast(mulp(cp,cq,cn, g, p.temp[1]))
    broadcast(players)
    for p in players:
        p.open_right = add(cp,cq,cn,p.broadcast, p.other)
        #print(p.open_left == p.open_right)


def multiply_beaver_without_check(players):
    n = Player.n
    for p in players:
        p.current_beaver_triple = p.beaver_triples.pop()
        p.set_broadcast((p.multiply_x[0] - p.current_beaver_triple[0][0]) % n)
    broadcast(players)
    for p in players:
        p.multiply_x_mask = (p.broadcast + p.other) % n
        p.set_broadcast((p.multiply_y[0] - p.current_beaver_triple[1][0]) % n)
    broadcast(players)
    for p in players:
        p.multiply_y_mask = (p.broadcast + p.other) % n
        p.beaver_multiply_local(p.multiply_x_mask, p.multiply_y_mask, p.current_beaver_triple)


def multiply_beaver_with_check(players):
    bits, n = Player.bits, Player.n
    multiply_beaver_without_check(players)
    while True:
        for p in players:
            p.beta = p.randkey(bits, n)
            p.set_broadcast(p.beta)
        broadcast(players)
        for p in players:
            p.beta = (p.broadcast + p.other) % n
        if players[0].beta != 0:
            break
    for p in players:
        #p.current_beaver_triple = p.beaver_triples.pop()
        p.a, p.b, p.c = p.current_beaver_triple
        p.d = (p.beta * p.multiply_x[0] - p.a[0]) % n
        p.set_broadcast(p.d)
    broadcast(players)
    for p in players:
        p.d = (p.broadcast + p.other) % n
        p.e = p.multiply_y_mask
        p.w = p.beta * p.product[0] - (p.e * p.a[0] + p.d * p.b[0] + p.d * p.e + p.c[0])
        p.set_broadcast(p.w)
    broadcast(players)
    for p in players:
        p.w = (p.broadcast + p.other) % n
    #print(players[0].w==0)


def multiply_beaver(players, need_check=False):
    if need_check:
        multiply_beaver_with_check(players)
    else:
        multiply_beaver_without_check(players)


def ecdsa_sign(players,need_check=False):
    cn,cp,cq,g, n = Player.cn, Player.cp, Player.cq, Player.g, Player.n
    for p in players:
        p.private_key = p.share_values.pop()
        p.k = p.share_values.pop()
        p.gamma = p.share_values.pop()
        p.set_multiply_x(p.k)
        p.set_multiply_y(p.gamma)
    multiply_beaver(players, need_check)
    for p in players:
        p.delta = p.product
        p.set_multiply_x(p.k)
        p.set_multiply_y(p.private_key)
    multiply_beaver(players, need_check)
    for p in players:
        p.sigma = p.product
        p.set_broadcast(p.delta)
    open_share_with_mac(players)
    for p in players:
        p.delta_inv = inv(p.open_value, n)
        p.k_inv = tuple((p.delta_inv * p.gamma[i])%n for i in range(2))
        p.k_inv_point = mulp(cp, cq, cn, g, p.k_inv[0])
        p.set_broadcast((p.k_inv_point, p.k_inv[1]))
    open_point_with_mac(players)
    for p in players:
        p.r_open = p.open_point[0]
        p.s = tuple(p.hash_message * p.k[i] + p.r_open * p.sigma[i] for i in range(2))
        p.set_broadcast(tuple(p.s))
    open_share_with_mac(players)
    for p in players:
        p.sign = (p.r_open, p.open_value)
        #print(p.sign)


if __name__ == "__main__":
    a = InputPlayer(10000)
    b = TrustedThirdParty(20000)
    c = ComputePlayer(50000)
    d = ComputePlayer(60000)

    times = 1
    a.set_message("hello world")
    b.generate_mac()
    b.generate_mac_share(times * 10)
    b.generate_beaver_triples(times*10)
    n = Player.n
    cp, cq, cn, g = Player.cp, Player.cq, Player.cn, Player.g
    t0 = time.time()
    for i in range(times):
        ecdsa_sign([c, d],need_check=True)

    t1 = time.time()
    t_with_check = t1-t0
    print('ecdsa time with check', t1-t0)
    t0 = time.time()
    for i in range(times):
        ecdsa_sign([c, d], need_check=False)
    t1 = time.time()
    t_without_check = t1 - t0
    print('ecdsa time without check', t_without_check)
    print(t_with_check/t_without_check)
