package workbench.nio.l08

import java.nio.channels.FileChannel
import java.nio.channels.WritableByteChannel

object FileSender {
    fun transferFully(file: FileChannel, position: Long, count: Long, target: WritableByteChannel): Int {
        var sent = 0L
        var calls = 0
        while (sent < count) {
            // may move fewer bytes than asked: keep going from where it stopped
            sent += file.transferTo(position + sent, count - sent, target)
            calls++
        }
        return calls
    }
}
