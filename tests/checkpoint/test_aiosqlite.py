import pytest
from langchain_core.runnables import RunnableConfig

from langgraph.channels.base import create_checkpoint
from langgraph.checkpoint.aiosqlite import AsyncSqliteSaver
from langgraph.checkpoint.base import Checkpoint, CheckpointMetadata, empty_checkpoint


class TestAsyncSqliteSaver:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.sqlite_saver = AsyncSqliteSaver.from_conn_string(":memory:")

        # objects for test setup
        self.config_1: RunnableConfig = {
            "configurable": {"thread_id": "thread-1", "thread_ts": "1"}
        }
        self.config_2: RunnableConfig = {
            "configurable": {"thread_id": "thread-2", "thread_ts": "2"}
        }

        self.chkpnt_1: Checkpoint = empty_checkpoint()
        self.chkpnt_2: Checkpoint = create_checkpoint(self.chkpnt_1, {}, 1)

        self.metadata_1: CheckpointMetadata = {
            "source": "input",
            "step": 2,
            "writes": {},
            "score": 1,
        }
        self.metadata_2: CheckpointMetadata = {
            "source": "loop",
            "step": 1,
            "writes": {"foo": "bar"},
            "score": None,
        }

    async def test_asearch(self):
        # set up test
        # save checkpoints
        await self.sqlite_saver.aput(self.config_1, self.chkpnt_1, self.metadata_1)
        await self.sqlite_saver.aput(self.config_2, self.chkpnt_2, self.metadata_2)

        # call method / assertions
        query_1: CheckpointMetadata = {"source": "input"}  # search by 1 key
        query_2: CheckpointMetadata = {
            "step": 1,
            "writes": {"foo": "bar"},
        }  # search by multiple keys
        query_3: CheckpointMetadata = {}  # search by no keys, return all checkpoints
        query_4: CheckpointMetadata = {"source": "update", "step": 1}  # no match

        async with self.sqlite_saver as sqlite_saver:
            search_results_1 = [
                c async for c in sqlite_saver.alist(None, filter=query_1)
            ]
            assert len(search_results_1) == 1
            assert search_results_1[0].metadata == self.metadata_1

            search_results_2 = [
                c async for c in sqlite_saver.alist(None, filter=query_2)
            ]
            assert len(search_results_2) == 1
            assert search_results_2[0].metadata == self.metadata_2

            search_results_3 = [
                c async for c in sqlite_saver.alist(None, filter=query_3)
            ]
            assert len(search_results_3) == 2

            search_results_4 = [
                c async for c in sqlite_saver.alist(None, filter=query_4)
            ]
            assert len(search_results_4) == 0

            # TODO: test before and limit params
