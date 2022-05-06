
from concurrent.futures import ProcessPoolExecutor as Pool
from multiprocessing import cpu_count, Lock

def main():
	pool = Pool(max_workers=cpu_count())
	x = []
	for _ in range(5):
		x.append(pool.submit(fct))

	for p in x:
		print(p.exception())

def fct():
	s = "hello world"
	print(sa)



if __name__ == "__main__":
    main()
