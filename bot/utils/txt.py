import aiofiles
from loguru import logger


async def load_file_lines(filename):
    data = []
    async with aiofiles.open(filename) as f:
        lines = await f.readlines()
        for line in lines:
            if (text := line.strip()):
                data.append(text)
    return data


async def big_file_reader(filename, lines_count: int = 5000):
    ids = []
    f = aiofiles.open(filename, 'r', encoding='utf8')
    async with aiofiles.open(filename, 'r', encoding='utf8') as f:
        count = 0
        async for line in f:
            try:
                if (text := line.strip()):
                    try:
                        num = int(text)
                    except ValueError:
                        pass
                    else:
                        ids.append(num)
                        count += 1
                if len(ids) >= lines_count:
                    yield ids
                    ids = []
            except Exception as e:
                logger.error('Err: {e}', e=e)
                break
