package workbench.reactive.l01

import reactor.adapter.JdkFlowAdapter
import reactor.core.publisher.Flux
import java.util.concurrent.Flow
import java.util.concurrent.SubmissionPublisher
import java.util.concurrent.TimeUnit

/** A subscriber that breaks rule 3.9 by calling request(0). Two publishers react differently. */
fun main() {
    SubmissionPublisher<Int>().use { jdk ->
        jdk.subscribe(RudeSubscriber("JDK SubmissionPublisher"))
        jdk.submit(1)
    }
    TimeUnit.MILLISECONDS.sleep(300)

    val reactor: Flow.Publisher<Int> = JdkFlowAdapter.publisherToFlowPublisher(Flux.range(1, 3))
    val rude = RudeSubscriber("Reactor Flux.range")
    reactor.subscribe(rude)
    TimeUnit.MILLISECONDS.sleep(300)
    if (!rude.signalled) println("Reactor Flux.range: no signal at all, the stream just stalls")
}

private class RudeSubscriber(private val name: String) : Flow.Subscriber<Int> {
    @Volatile var signalled = false

    override fun onSubscribe(s: Flow.Subscription) = s.request(0)   // rule 3.9 says: must be > 0
    override fun onNext(item: Int) { signalled = true; println("$name: onNext $item") }
    override fun onError(t: Throwable) { signalled = true; println("$name: onError $t") }
    override fun onComplete() { signalled = true; println("$name: onComplete") }
}
