package workbench.ledger.l03

import java.util.concurrent.Callable
import java.util.concurrent.Executors
import java.util.concurrent.RejectedExecutionException

/** What the client gets back for one transfer request. */
enum class Status { APPLIED, INSUFFICIENT_FUNDS, DECLINED, TIMED_OUT, BUSY }

data class Reply(val transferId: String, val status: Status, val standIn: Boolean = false)

/**
 * The front of the service: one virtual thread per request. Each request is screened, then handed
 * to the bounded ledger pool from lesson 2, which journals it and applies it.
 */
class TransferServer(private val ledger: LedgerService, private val screening: Screening) {

    /** Handles one request on the calling thread. You don't need to change this. */
    fun handle(t: Transfer): Reply {
        val verdict = screening.screen(t)                        // 1. fraud and limits, one deadline
        if (verdict == Verdict.DECLINED) return Reply(t.id(), Status.DECLINED)
        if (verdict == Verdict.TIMED_OUT) return Reply(t.id(), Status.TIMED_OUT)
        val outcome = try {
            ledger.submit(t).get()                               // 2. no timeout: once the ledger has it, money may move
        } catch (e: RejectedExecutionException) {
            return Reply(t.id(), Status.BUSY)                    // 3. pool full: 503, the client retries with the same id
        }
        val status = if (outcome == Outcome.APPLIED) Status.APPLIED else Status.INSUFFICIENT_FUNDS
        return Reply(t.id(), status, standIn = verdict == Verdict.STAND_IN)
    }

    fun serveAll(requests: List<Transfer>): List<Reply> =
        Executors.newVirtualThreadPerTaskExecutor().use { perRequest ->
            val replies = requests.map { t -> perRequest.submit(Callable { handle(t) }) }   // 1. start every request
            replies.map { it.get() }                                                       // 2. then wait, in order
        }                                                                                   // 3. close() waits for all
}
