package workbench.nio.l08

import java.nio.channels.FileChannel
import java.nio.channels.WritableByteChannel

object FileSender {
    /**
     * Send `count` bytes of [file], starting at [position], to [target] with `FileChannel.transferTo`.
     * On Linux, a socket target makes the JDK use `sendfile(2)`: the kernel moves the bytes from the
     * page cache to the socket without copying them through your process.
     *
     * `transferTo` may transfer FEWER bytes than asked (a full socket buffer, a slow channel), so call
     * it in a loop until all `count` bytes are sent. Return how many times you called `transferTo`.
     */
    fun transferFully(file: FileChannel, position: Long, count: Long, target: WritableByteChannel): Int =
        TODO("loop over file.transferTo until count bytes are sent")
}
