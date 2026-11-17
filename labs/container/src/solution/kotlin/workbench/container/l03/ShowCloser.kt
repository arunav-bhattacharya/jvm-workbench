package workbench.container.l03

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

/** Closes the box office after a show. It has no interface, so the container intercepts it with a subclass. */
@Component
open class ShowCloser(private val archive: ShowArchive) {             // open: a subclass may extend it
    @Timed
    open fun close(night: String): String {                           // open: a subclass may override it
        verify(night)                      // a self-call: intercepted, because the subclass IS this object
        archive.file(night)
        return "closed $night"
    }

    @Timed
    open fun verify(night: String) = check(night.startsWith("N-")) { "bad night id $night" }

    fun hall(): String = "Main hall"       // not intercepted, so it may stay final
}
