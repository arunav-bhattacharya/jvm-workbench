package workbench.memory.l03

import java.util.WeakHashMap

data class KSession(val id: String)
data class KCheckoutState(val cart: String)
data class KSessionAudit(val session: KSession, val note: String)  // refers back to its own key

/** WeakHashMap drops an entry when its key is unreachable, unless the value refers to the key. */
fun main() {
    val checkouts = WeakHashMap<KSession, KCheckoutState>()
    val audits = WeakHashMap<KSession, KSessionAudit>()
    var s1: KSession? = KSession("s-1")
    var s2: KSession? = KSession("s-2")
    checkouts[s1!!] = KCheckoutState("2 items")
    audits[s2!!] = KSessionAudit(s2, "opened")

    s1 = null                                                      // the sessions end: nothing else refers to them
    s2 = null
    repeat(5) { System.gc(); Thread.sleep(20) }                    // demo only: ask for a few GCs

    println("checkouts left: ${checkouts.size}")                   // size also removes cleared entries
    println("audits left:    ${audits.size}")
}
