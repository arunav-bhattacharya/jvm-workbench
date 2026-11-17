package workbench.patterns.l02

// A factory over a sealed family, and the same factory passed around as a function.

enum class Channel { SMS, EMAIL, FAKE }

sealed interface Messenger {
    fun send(to: String, text: String): String

    companion object {
        // the factory: an exhaustive when over the enum, with no else branch
        fun of(c: Channel): Messenger = when (c) {
            Channel.SMS -> SmsMessenger()
            Channel.EMAIL -> EmailMessenger()
            Channel.FAKE -> FakeMessenger()
        }
    }
}

class SmsMessenger : Messenger {
    override fun send(to: String, text: String) = "sms to $to: $text"
}
class EmailMessenger : Messenger {
    override fun send(to: String, text: String) = "email to $to: $text"
}
class FakeMessenger : Messenger {
    override fun send(to: String, text: String) = "fake: nothing sent"
}

// the modern "factory method": the caller hands in how to make the product
class OrderNotices(private val messengers: () -> Messenger) {
    fun orderLeft(customer: String) = messengers().send(customer, "your order is on its way")
}

fun main() {
    for (c in Channel.entries) {
        println("$c -> ${Messenger.of(c).send("anna", "your order is on its way")}")
    }
    println("test notices -> ${OrderNotices(::FakeMessenger).orderLeft("anna")}")
}
