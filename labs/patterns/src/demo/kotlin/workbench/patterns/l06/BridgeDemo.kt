package workbench.patterns.l06

// Notices (what to say) and channels (how it travels) vary on their own: 2 + 2 pieces, not 2 x 2.

// the implementor side: one method, so a lambda is enough
fun interface NoticeChannel { fun deliver(to: String, body: String): String }

private val sms = NoticeChannel { to, body -> "SMS   to $to: $body" }
private val email = NoticeChannel { to, body -> "EMAIL to $to: $body" }

// the abstraction side: what to say. Each notice HOLDS a channel instead of being one.
sealed interface ShopNotice {
    val channel: NoticeChannel
    fun send(to: String): String

    data class OnItsWay(override val channel: NoticeChannel, val orderNo: String, val courier: String) : ShopNotice {
        override fun send(to: String) = channel.deliver(to, "order $orderNo is on its way with $courier")
    }

    data class SoldOut(override val channel: NoticeChannel, val item: String, val days: Int) : ShopNotice {
        override fun send(to: String) = channel.deliver(to, "$item is sold out, back in $days days")
    }
}

fun main() {
    val channels = listOf(sms, email)
    for (ch in channels) {
        println(ShopNotice.OnItsWay(ch, "7781", "Pedal Post").send("Ana"))
        println(ShopNotice.SoldOut(ch, "rye bread", 2).send("Ben"))
    }
}
