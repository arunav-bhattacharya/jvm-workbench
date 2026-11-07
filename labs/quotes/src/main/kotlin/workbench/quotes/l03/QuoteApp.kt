package workbench.quotes.l03

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.runBlocking
import kotlin.coroutines.CoroutineContext
import kotlin.time.Duration

/** The whole program: the Netty server from lesson 1 in front of the coroutine service. */
class QuoteApp(
    providers: List<Provider>,
    deadline: Duration,
    maxInFlight: Int,
    loops: Int = 1,
    context: CoroutineContext = Dispatchers.Default,
) {
    val service = QuoteService(context, BestQuote(providers, deadline), maxInFlight)
    val server = QuoteServer(loops, service)

    fun port(): Int = server.port()

    /** Stop in order. Called from a shutdown hook, which is an edge, so runBlocking is fine here. */
    fun shutdown(grace: Duration) {
        server.stopAccepting()                                       // 1. no new connections
        runBlocking { service.shutdown(grace) }                      // 2. drain what is in flight, cancel the rest
        server.close()                                               // 3. close the connections, stop the loops
    }
}
