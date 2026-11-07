package workbench.patterns.l09

// A merchant payout as a state machine: states and events are data, the rules are one pure function.

sealed interface PayoutState {
    data class Requested(val id: String, val amountMinor: Long) : PayoutState
    data class Approved(val id: String, val amountMinor: Long, val approver: String) : PayoutState
    data class Sent(val id: String, val amountMinor: Long, val bankRef: String) : PayoutState
    data class Settled(val id: String, val amountMinor: Long) : PayoutState
    data class Returned(val id: String, val reason: String) : PayoutState
}

sealed interface PayoutEvent {
    data class Approve(val approver: String) : PayoutEvent
    data class Send(val bankRef: String) : PayoutEvent
    data object Confirm : PayoutEvent
    data class BankReturn(val reason: String) : PayoutEvent
}

private fun next(s: PayoutState, e: PayoutEvent): PayoutState = when (s) {   // no else: a new state breaks the build
    is PayoutState.Requested -> when (e) {
        is PayoutEvent.Approve if e.approver.isNotBlank() -> PayoutState.Approved(s.id, s.amountMinor, e.approver)
        else -> throw illegal(s, e)
    }
    is PayoutState.Approved -> when (e) {
        is PayoutEvent.Send -> PayoutState.Sent(s.id, s.amountMinor, e.bankRef)
        else -> throw illegal(s, e)
    }
    is PayoutState.Sent -> when (e) {
        PayoutEvent.Confirm -> PayoutState.Settled(s.id, s.amountMinor)
        is PayoutEvent.BankReturn -> PayoutState.Returned(s.id, e.reason)
        else -> throw illegal(s, e)
    }
    is PayoutState.Settled, is PayoutState.Returned -> throw illegal(s, e)    // terminal
}

// a second when over the same states: the API's status label
private fun label(s: PayoutState): String = when (s) {
    is PayoutState.Requested -> "pending approval"
    is PayoutState.Approved -> "approved by ${s.approver}"
    is PayoutState.Sent -> "sent, bank ref ${s.bankRef}"
    is PayoutState.Settled -> "settled"
    is PayoutState.Returned -> "returned: ${s.reason}"
}

private fun illegal(s: PayoutState, e: PayoutEvent) =
    IllegalStateException("${e::class.simpleName} not allowed in ${s::class.simpleName}")

fun main() {
    var s: PayoutState = PayoutState.Requested("po-31", 125_000)
    println(label(s))
    for (e in listOf(PayoutEvent.Approve("dana"), PayoutEvent.Send("DE-REF-0091"), PayoutEvent.Confirm)) {
        s = next(s, e)
        println(label(s))
    }
    try {
        next(PayoutState.Requested("po-32", 900), PayoutEvent.Send("DE-REF-0092"))
    } catch (ex: IllegalStateException) {
        println("rejected: ${ex.message}")
    }
}
