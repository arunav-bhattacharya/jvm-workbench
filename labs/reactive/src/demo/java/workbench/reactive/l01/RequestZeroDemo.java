package workbench.reactive.l01;

import reactor.adapter.JdkFlowAdapter;
import reactor.core.publisher.Flux;

import java.util.concurrent.Flow;
import java.util.concurrent.SubmissionPublisher;
import java.util.concurrent.TimeUnit;

/** A subscriber that breaks rule 3.9 by calling request(0). Two publishers react differently. */
public class RequestZeroDemo {
    public static void main(String[] args) throws Exception {
        try (SubmissionPublisher<Integer> jdk = new SubmissionPublisher<>()) {
            jdk.subscribe(new Rude("JDK SubmissionPublisher"));
            jdk.submit(1);
        }
        TimeUnit.MILLISECONDS.sleep(300);

        Flow.Publisher<Integer> reactor = JdkFlowAdapter.publisherToFlowPublisher(Flux.range(1, 3));
        Rude rude = new Rude("Reactor Flux.range");
        reactor.subscribe(rude);
        TimeUnit.MILLISECONDS.sleep(300);
        if (!rude.signalled) System.out.println("Reactor Flux.range: no signal at all, the stream just stalls");
    }

    static final class Rude implements Flow.Subscriber<Integer> {
        final String name;
        volatile boolean signalled;
        Rude(String name) { this.name = name; }

        @Override public void onSubscribe(Flow.Subscription s) { s.request(0); }   // rule 3.9 says: must be > 0
        @Override public void onNext(Integer item) { signalled = true; System.out.println(name + ": onNext " + item); }
        @Override public void onError(Throwable t) { signalled = true; System.out.println(name + ": onError " + t); }
        @Override public void onComplete() { signalled = true; System.out.println(name + ": onComplete"); }
    }
}
