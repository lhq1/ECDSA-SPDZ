from player import *
from threading import Thread
from ecc.elliptic import inv,mulp,add

import time

elliptic_time = 0
broadcast_time = 0
random_number = 0


def broadcast(players):
    #players = ComputePlayer.ComputeList
    #print(players[0].rec_port, players[1].rec_port)
    global broadcast_time
    t_start = time.time()
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
    t_end = time.time()
    broadcast_time += t_end - t_start


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
        assert p.mac_check==0


def open_point_with_mac(players):
    global elliptic_time
    n, cp, cq, cn, g = Player.n, Player.cp, Player.cq, Player.cn, Player.g
    for p in players:
        p.temp = p.broadcast
        p.set_broadcast(p.temp[0])
    broadcast(players)
    t0 = time.time()
    for p in players:
        p.open_point = add(cp, cq, cn, p.broadcast, p.other)
        p.open_left = mulp(cp, cq, cn, p.open_point, p.alpha)
        p.open_right = mulp(cp, cq, cn, g, p.temp[1])
        p.set_broadcast((p.open_left, p.open_right))
    t1 = time.time()
    elliptic_time += t1 - t0

    broadcast(players)

    t0 = time.time()
    for p in players:
        p.open_left = add(cp, cq, cn, p.broadcast[0], p.other[0])
        p.open_right = add(cp,cq,cn,p.broadcast[1], p.other[1])
        assert p.open_left==p.open_right
        #print(p.open_left == p.open_right)
    t1 = time.time()
    elliptic_time += t1 - t0


def multiply_beaver_without_check(players):
    n = Player.n
    for p in players:
        p.current_beaver_triple = p.beaver_triples.pop()
        p.first_send = (p.multiply_x[0] - p.current_beaver_triple[0][0]) % n
        p.second_send = (p.multiply_y[0] - p.current_beaver_triple[1][0]) % n
        p.set_broadcast((p.first_send, p.second_send))
    broadcast(players)
    for p in players:
        p.multiply_x_mask = (p.broadcast[0] + p.other[0]) % n
        p.multiply_y_mask = (p.broadcast[1] + p.other[1]) % n
        p.beaver_multiply_local(p.multiply_x_mask, p.multiply_y_mask, p.current_beaver_triple)


def multiply_beaver_without_check_parallel(players, number):
    n = Player.n
    for p in players:
        p.list_send = []
        p.list_triple = []
        for i in range(number):
            p.current_beaver_triple = p.beaver_triples.pop()
            p.first_send = (p.multiply_x[0][i] - p.current_beaver_triple[0][0]) % n
            p.second_send = (p.multiply_y[0][i] - p.current_beaver_triple[1][0]) % n
            p.list_send.append((p.first_send, p.second_send))
            p.list_triple.append(p.current_beaver_triple)
        p.set_broadcast(p.list_send)
    broadcast(players)
    for p in players:
        p.list_product = []
        for i in range(number):
            p.multiply_x_mask = (p.broadcast[i][0] + p.other[i][0]) % n
            p.multiply_y_mask = (p.broadcast[i][1] + p.other[i][1]) % n
            p.beaver_multiply_local(p.multiply_x_mask, p.multiply_y_mask, p.current_beaver_triple)
            p.list_product.append(p.product)


def multiply_beaver_with_check(players):
    global random_number
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
        if p.compute_no == 0:
            p.w = p.beta * p.product[0] - (p.e * p.a[0] + p.d * p.b[0] + p.d * p.e + p.c[0])
        else:
            p.w = p.beta * p.product[0] - (p.e * p.a[0] + p.d * p.b[0]  + p.c[0])
        p.set_broadcast(p.w)
    broadcast(players)
    for p in players:
        p.w = (p.broadcast + p.other) % n
        #print(players[0].w)
        assert p.w == 0


def multiply_beaver_with_check_parallel(players,num):
    bits, n = Player.bits, Player.n
    multiply_beaver_without_check_parallel(players,num)
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
        p.list_temp = []
        for i in range(num):
            p.current_beaver_triple = p.list_triple[i]
            p.a, p.b, p.c = p.current_beaver_triple
            p.list_temp.append((p.beta * p.list_send[i][0] - p.a[0]) % n)
        p.set_broadcast(p.list_temp)
    broadcast(players)
    for p in players:
        p.list_temp = []
        for i in range(num):
            p.d = (p.broadcast[i] + p.other[i]) % n
            p.e = p.list_send[i][1]
            p.w = p.beta * p.list_product[i][0] - (p.e * p.a[0] + p.d * p.b[0] + p.d * p.e + p.c[0])
            p.list_temp.append(p.w)
        p.set_broadcast(p.list_temp)
    broadcast(players)
    for p in players:
        for i in range(num):
            p.w = (p.broadcast[i] + p.other[i]) % n
    #print(players[0].w==0)


def multiply_beaver(players,need_check=False):
    if need_check:
        multiply_beaver_with_check(players)
    else:
        multiply_beaver_without_check(players)


def multiply_beaver_parallel(players, number, need_check=False):
    if need_check:
        multiply_beaver_with_check_parallel(players,number)
    else:
        multiply_beaver_without_check_parallel(players, number)


def ecdsa_keygen(players):
    cn, cp, cq, g, n = Player.cn, Player.cp, Player.cq, Player.g, Player.n
    for p in players:
        p.private_key = p.share_values.pop()
        p.public_key = mulp(cp, cq, cn, g, p.private_key[0])


def ecdsa_sign(players,need_check=False):
    global elliptic_time
    cn,cp,cq,g, n = Player.cn, Player.cp, Player.cq, Player.g, Player.n
    for p in players:
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

    t_start = time.time()
    for p in players:
        p.k_inv_point = mulp(cp, cq, cn, g, p.k_inv[0])
        p.set_broadcast((p.k_inv_point, p.k_inv[1]))
    t_end = time.time()
    elliptic_time += t_end - t_start

    open_point_with_mac(players)
    for p in players:
        p.r_open = p.open_point[0]
        p.s = tuple(p.hash_message * p.k[i] + p.r_open * p.sigma[i] for i in range(2))
        p.set_broadcast(tuple(p.s))
    open_share_with_mac(players)
    for p in players:
        p.sign = (p.r_open, p.open_value)
        #print(p.sign)


def ecdsa_sign_parallel(players,need_check=False):
    global elliptic_time
    cn,cp,cq,g, n = Player.cn, Player.cp, Player.cq, Player.g, Player.n
    for p in players:
        p.k = p.share_values.pop()
        p.gamma = p.share_values.pop()
        p.set_multiply_x([p.k, p.k])
        p.set_multiply_y([p.gamma, p.private_key])
    multiply_beaver_parallel(players, 2, need_check)
    for p in players:
        p.delta = p.list_product[0]
        p.sigma = p.list_product[1]
        p.set_broadcast(p.delta)
    open_share_with_mac(players)
    for p in players:
        p.delta_inv = inv(p.open_value, n)
        p.k_inv = tuple((p.delta_inv * p.gamma[i]) %n for i in range(2))
    t0 = time.time()
    for p in players:
        p.k_inv_point = mulp(cp, cq, cn, g, p.k_inv[0])
        p.set_broadcast((p.k_inv_point, p.k_inv[1]))
    t1 = time.time()
    elliptic_time += t1 - t0
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
    c = ComputePlayer(21000)
    d = ComputePlayer(31000)

    times = 64
    pattern = (0,1,2,3)
    a.set_message("hello world")
    b.generate_mac()
    b.generate_mac_share(4+times * 8)
    b.generate_beaver_triples(times*8)

    n = Player.n
    cp, cq, cn, g = Player.cp, Player.cq, Player.cn, Player.g
    if 0 in pattern:
        broadcast_time = 0
        elliptic_time = 0
        t0 = time.time()
        ecdsa_keygen([c,d])
        for i in range(times):
            ecdsa_sign([c, d],need_check=True)
        t1 = time.time()
        t_with_check = t1-t0
        print('ecdsa time with check', t1-t0)
        print('broadcast time: {}, ratio:{}'.format(broadcast_time, broadcast_time / t_with_check))
        print("elliptic_operation: {}, ratio: {}".format(elliptic_time, elliptic_time / t_with_check))
    if 1 in pattern:
        broadcast_time = 0
        elliptic_time = 0
        t0 = time.time()
        ecdsa_keygen([c,d])
        for i in range(times):
            ecdsa_sign([c, d], need_check=False)
        t1 = time.time()
        t_without_check = t1 - t0
        print('ecdsa time without check', t_without_check)
        print('broadcast time: {}, ratio:{}'.format(broadcast_time, broadcast_time/t_without_check))
        print("elliptic_operation: {}, ratio: {}".format(elliptic_time, elliptic_time/t_without_check))

    if 2 in pattern:
        broadcast_time = 0
        elliptic_time = 0
        t0 = time.time()
        ecdsa_keygen([c,d])
        for i in range(times):
            ecdsa_sign_parallel([c, d], need_check=True)
        t1 = time.time()
        t_with_check_parallel = t1-t0
        print('ecdsa time with check(parallel)', t1-t0)
        print('broadcast time: {}, ratio:{}'.format(broadcast_time, broadcast_time / t_with_check_parallel))
        print("elliptic_operation: {}, ratio: {}".format(elliptic_time, elliptic_time / t_with_check_parallel))

    if 3 in pattern:
        broadcast_time = 0
        elliptic_time = 0
        t0 = time.time()
        ecdsa_keygen([c,d])
        for i in range(times):
            ecdsa_sign_parallel([c, d], need_check=False)
        t1 = time.time()
        t_without_check_parallel = t1 - t0
        print('ecdsa time without check(parallel)', t_without_check_parallel)
        print('broadcast time: {}, ratio:{}'.format(broadcast_time, broadcast_time / t_without_check_parallel))
        print("elliptic_operation: {}, ratio: {}".format(elliptic_time, elliptic_time / t_without_check_parallel))

    if 0 in pattern and 1 in pattern:
        print(t_with_check/t_without_check)
    if 2 in pattern and 3 in pattern:
        print(t_with_check_parallel / t_without_check_parallel)
