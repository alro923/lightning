# Copyright The PyTorch Lightning team.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import queue
from typing import Any, Dict, Optional

from pytorch_lightning.plugins.io.checkpoint_plugin import CheckpointIO
from pytorch_lightning.plugins.io.wrapper import _WrappingCheckpointIO
from pytorch_lightning.utilities.cloud_io import _ThreadQueue
from pytorch_lightning.utilities.types import _PATH


class AsyncCheckpointIO(_WrappingCheckpointIO, CheckpointIO):
    """AsyncCheckpointIO enablses saving the checkpoints asynchronously.

    .. warning::

        This is currently an experimental plugin/feature and API changes are to be expected.

    Args:
        checkpoint_io: A checkpoint IO plugin that is used as the basis for async checkpointing.
        interval: Sleep time between each queue check.
    """

    def __init__(self, checkpoint_io: Optional["CheckpointIO"] = None, interval: float = 2.0) -> None:
        super().__init__(checkpoint_io)

        self._thread = _ThreadQueue(q=queue.Queue(), interval=interval)
        self._thread.start()

    def save_checkpoint(self, checkpoint: Dict[str, Any], path: _PATH, storage_options: Optional[Any] = None) -> None:
        """Save model/training states as a checkpoint file through state-dump and file-write.

        Args:
            checkpoint: dict containing model and trainer state
            path: write-target path
            storage_options: not used in ``TorchCheckpointIO.save_checkpoint``
        """
        self._thread._queue.put((self.checkpoint_io.save_checkpoint, (checkpoint, path)))

    def remove_checkpoint(self, path: _PATH) -> None:
        """Remove checkpoint file from the filesystem.

        Args:
            path: Path to checkpoint
        """
        return self._checkpoint_io.remove_checkpoint(path)

    def load_checkpoint(self, path: _PATH, storage_options: Optional[Any] = None) -> Dict[str, Any]:
        """Loads checkpoint using :func:`torch.load`, with additional handling for ``fsspec`` remote loading of
        files.

        Args:
            path: Path to checkpoint
            map_location: a function, :class:`torch.device`, string or a dict specifying how to remap storage
            locations.

        Returns: The loaded checkpoint.
        """
        return self._checkpoint_io.load_checkpoint(path, storage_options)

    def teardown(self) -> None:
        """This method is called to close the threads."""
        self._thread.join()
