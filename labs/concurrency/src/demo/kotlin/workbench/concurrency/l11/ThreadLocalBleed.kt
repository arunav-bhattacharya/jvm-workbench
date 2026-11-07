package workbench.concurrency.l11

import java.util.concurrent.Executors

// Six requests on a pool of one reused thread. The handler sets the user only when the request
// carries one. A pool of 1 makes the bug happen every time; a pool of 200 makes it rare and random.
private val USER = ThreadLocal<String>()

private fun leaky(user: String?): String {
    if (user != null) USER.set(user)
    return "request($user) ran as ${USER.get()}"
}

private fun clean(user: String?): String {
    if (user != null) USER.set(user)
    try {
        return "request($user) ran as ${USER.get()}"
    } finally {
        USER.remove()                                        // leave the thread as you found it
    }
}

fun main() {
    val requests = listOf("alice", null, "bob", null, null, "carol")
    for (handler in listOf(::leaky, ::clean)) {
        val pool = Executors.newSingleThreadExecutor()
        println("---")
        for (user in requests) println("  " + pool.submit<String> { handler(user) }.get())
        pool.shutdown()
    }
}
