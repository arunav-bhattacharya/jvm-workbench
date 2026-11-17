package workbench.container.l02

import java.util.concurrent.CopyOnWriteArrayList

/** Where each night's papers go once the show is over. */
@Component
class ShowArchive {
    private val filed = CopyOnWriteArrayList<String>()

    fun file(night: String) {
        filed += night
    }

    fun filed(): List<String> = filed.toList()
}

/**
 * Closes the box office after a show. It has no interface, so the container intercepts it with a
 * Byte Buddy subclass. Once your check() works, the container refuses this class: read the message.
 */
@Component
class ShowCloser(private val archive: ShowArchive) {
    @Timed
    fun close(night: String): String {
        verify(night)                      // a self-call
        archive.file(night)
        return "closed $night"
    }

    @Timed
    fun verify(night: String) = check(night.startsWith("N-")) { "bad night id $night" }

    fun hall(): String = "Main hall"
}
