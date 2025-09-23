"""
Data pool will provide a series of data share methods which are able to be used in multiple processes.
Once a shared data is registered in datapool, it will be available in all running processes.

We also provide read-only mode for a shared DataBlock, and this will improve performance in some simple
usage scenarios.

Each of shared DataBlock has a unique name.
"""

import multiprocessing as mp
import multiprocessing.shared_memory as sm
import numpy as np
import time
import logging as log

class C_DataPool:
    size = 30

"""
SharedList is constructed with a series of string:
     - string format: name;shape;dtype;domain;read_on_copy
     - example: /expmatrix;1,3,3;int32;process1;1
     - example: /explist;14;list;process2;0
"""

Length = C_DataPool.size
SharedList = sm.ShareableList([" " * 100] * Length)
MainProcessId = mp.current_process().pid

Index = mp.Value('i', -1)


def close_pool():
    DataBlock.RUNNING_STATE = False
    DataBlock.close_all()
    SharedList.shm.close()
    if mp.current_process().pid == MainProcessId:
        SharedList.shm.unlink()


def put(data):
    with Index:
        Index.value += 1
        Index.value %= Length
        SharedList[Index.value] = data
        log.debug('[%d]Put shared message: %s' % (Index.value, data))


class DataPoolError(Exception): pass
class DuplicateName(DataPoolError): pass
class FormatNotSupport(DataPoolError): pass
class DataNameEmpty(DataPoolError): pass
class BlockNotExist(DataPoolError): pass
class UnsupportDataFormat(DataPoolError): pass

class DataBlock(object):
    _blocks_dict = {}
    _index = -1
    RUNNING_STATE = True

    def __init__(self, data: np.ndarray | list | tuple = None,
                 name: str | None = None,
                 read_on_copy=False) -> None:
        """
        name is the unique identifier of data in shared memory space, or shared message from SharedList.
        data is the data (now is only support for the numpy and list format)

        the list and tuple must in One-dimensional, and the elements must in python-build-in data type:

            int (signed 64-bit)
            float
            bool
            str (less than 10M bytes each when encoded as UTF-8)
            bytes (less than 10M bytes each)
            None
            (same as ShareableList)

        the list will be transferred to ShareableList to shared, so that it cannot
        change the number of elements, but can change the contents in it.
        """

        self._available = True

        if data is None:
            """
            Create new DataBlock from shared memory, the name fild is treated as the shared message.
            """

            if name is None:
                raise DataNameEmpty("Getting data from shared memory requires the name field!")
            self._name, _shape_or_size, self._type_str, self._process_domain, self._read_on_copy = name.split(';')
            self._read_on_copy = True if self._read_on_copy == "1" else False
            if self._type_str in ['list', 'tuple']:
                self._shape_or_size = int(_shape_or_size)
                self._bind_data = sm.ShareableList(name=self._name)
                self._shared_mem = self._bind_data.shm
            else:
                # ndarray
                self._shape_or_size = tuple(map(int, _shape_or_size.split(',')))
                self._shared_mem = sm.SharedMemory(self._name)
                self._bind_data = np.ndarray(self._shape_or_size, dtype=self._type_str, buffer=self._shared_mem.buf)
                # self.__getitem__ = lambda *args, **kwargs: self._bind_data.__getitem__(*args, **kwargs)
                # self.__setitem__ = lambda key, value: self._bind_data.__setitem__(key, value)

            return

        """
        Create new DataBlock from local data.
        """

        if self._blocks_dict.get(name, None) is not None:
            raise DuplicateName(name)

        if isinstance(data, (list, tuple)):

            self._type_str = f'{type(data)}'.removeprefix("<class '").removesuffix("'>")
            self._bind_data = sm.ShareableList(data, name=name)
            self._name = self._bind_data.shm.name
            self._shape_or_size = len(data)
            self._shared_mem = data.shm

        elif isinstance(data, np.ndarray):

            self._type_str = f"{data.dtype}"
            self._shape_or_size = data.shape  # ",".join(map(str,data.shape))
            self._shared_mem = sm.SharedMemory(create=True, size=data.nbytes, name=name)  # 可能会出现名字重复的错误
            self._name = self._shared_mem.name
            self._bind_data = np.ndarray(data.shape, dtype=data.dtype, buffer=self._shared_mem.buf)

            # self.__getitem__ = lambda *args, **kwargs: self._bind_data.__getitem__(*args, **kwargs)
            # self.__setitem__ = lambda key, value: self._bind_data.__setitem__(key, value)

        else:
            raise FormatNotSupport(type(data))

        self._process_domain = mp.current_process().pid
        self._read_on_copy = read_on_copy  # 控制在读取bind_data时的操作是复制数据到本地（True）还是直接使用共享内存中的数据（False）

        if self._type_str == 'tuple': self._read_on_copy = True

    def close(self):
        if self._process_domain == mp.current_process().pid:
            self._shared_mem.close()
            self._shared_mem.unlink()
        else:
            self._shared_mem.close()

        self._blocks_dict.pop(self._name)
        self._available = False

    def __del__(self):
        if self._available:
            self.close()

    def __getitem__(self, index):

        if self._type_str in ['list', 'tuple']:

            """
            for list and tuple type
            """

            assert isinstance(int, index)

            if 0 <= index < self._shape_or_size:
                return self._bind_data[index]
            raise IndexError(f'Out of boundary! 0 <= {index} < {self._shape_or_size}')

        else:

            """
            for numpy
            """

            return self._bind_data[index]

    def __setitem__(self, index, value):

        if self._type_str in ['list', 'tuple']:
            """
            for list and tuple type
            """

            assert isinstance(int, index)

            if 0 <= index < self._shape_or_size:
                if isinstance(value, [str, bytes, bool, int, float, None.__class__]):
                    self._bind_data[index] = value
                else:
                    raise UnsupportDataFormat(type(value))

            raise IndexError(f'Out of boundary! 0 <= {index} < {self._shape_or_size}')

        else:

            """
            for numpy
            """

            self._bind_data[index] = value

    def push(self):
        """
        upload this source to shared memory space
        """
        obj = self._blocks_dict.get(self._name, None)
        if obj is not None:
            if obj == self:
                log.warn(f'You have already register this resource. ({self._name})')
            else:
                raise DuplicateName(self._name)
        else:
            self._blocks_dict[self._name] = self
            if self._type_str in ['list', 'tuple']:
                msg = f"{self._name};{self._shape_or_size};{self._type_str};{self._process_domain};{1 if self._read_on_copy else 0}"
            else:
                shape = ",".join(map(str, self._shape_or_size))
                msg = f"{self._name};{shape};{self._type_str};{self._process_domain};{1 if self._read_on_copy else 0}"
            put(msg)

    @property
    def Name(self):
        return self._name

    @property
    def Type(self):
        return self._type_str

    @property
    def TypeClass(self):
        if self._type_str == 'list':
            return list
        if self._type_str == 'tuple':
            return tuple

        # numpy
        return getattr(np, self._type_str)

    @property
    def Data(self):
        if self._read_on_copy:
            if self._type_str in ['tuple', 'list']:
                _t = []
                for item in self._bind_data:
                    _t.append(item)
                if self._type_str == 'tuple':
                    return tuple(_t)
                return _t
            else:
                return self._bind_data.copy()
        elif self._type_str == 'tuple':
            log.warn('Tuple type does not support get the raw data from shared space, a copy item will be return, and\
                      "self._read_on_copy" is changed to True by default to avoid next warnning message.')
            self._read_on_copy = True
            return self.Data
        else:
            return self._bind_data

    @classmethod
    def get_block(cls, name):
        obj: cls = cls._blocks_dict.get(name, None)
        if obj is None:
            raise BlockNotExist(name)
        return obj

    @classmethod
    def items(cls):
        return cls.items()

    """
    Work Thread: receive and update shared data list.
    """

    @classmethod
    def work_thread(cls):
        cls._index = -1
        tik = 0
        cls.RUNNING_STATE = True
        while cls.RUNNING_STATE:
            tik += 1
            if tik > 30:
                tik = 0
                cls.check_alive()

            if cls._index == Index.value:
                time.sleep(1)
                continue

            cls._index += 1
            cls._index %= Length

            share_str = SharedList[cls._index]
            block = cls(name=share_str)
            cls._blocks_dict[block._name] = block

    @classmethod
    def close_all(cls):
        all_names = cls._blocks_dict.keys()
        objs = [cls._blocks_dict[name] for name in all_names]
        for o in objs:
            o.close()

    @classmethod
    def check_alive(cls):
        for i in range(3):
            try:
                for name in cls._blocks_dict.keys():
                    try:
                        _o = sm.SharedMemory(name)
                    except FileNotFoundError:
                        obj = cls._blocks_dict.pop()

                        obj.close()
                log.debug("Datablock Checking finished!")
                break
            except Exception as e:
                log.error(f'Error occurred: {e}')
                log.debug(f'[Re-try {i + 1}] Re-check the data.')


def datapool_threading():
    import threading
    t = threading.Thread(target=DataBlock.work_thread, daemon=True)
    t.start()


# test code
if __name__ == '__main__':
    from multiprocessing import Process

    log.basicConfig(level=log.DEBUG)


    def f1():
        data_array = np.zeros((1, 2, 3), np.int64)
        db = DataBlock(data=data_array, name='test1')
        db.push()
        for i in range(50):
            time.sleep(1)
            log.info(f'{db.Data[0, 0, 0]}')
        close_pool()


    def f2():
        datapool_threading()
        while True:
            try:
                time.sleep(2)
                data_array = DataBlock.get_block('test1').Data
                break
            except:
                continue

        for i in range(30):
            data_array[0, 0, 0] = data_array[0, 0, 0] + i
            time.sleep(0.5)

        close_pool()


    log.info('Start Testing....')
    t1 = Process(target=f1, daemon=True)
    t2 = Process(target=f2, daemon=True)
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    close_pool()
    log.info('End Testing....')