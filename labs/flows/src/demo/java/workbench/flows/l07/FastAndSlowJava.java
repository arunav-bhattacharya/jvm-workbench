package workbench.flows.l07;

import java.util.ArrayList;
import java.util.List;
import org.reactivestreams.Subscription;
import reactor.core.publisher.BaseSubscriber;
import reactor.core.publisher.Sinks;

// Java equivalent: Reactor multicast sinks with one fast subscriber and one slow one.
// The slow diary keeper asks for one announcement and then nothing more until the end,
// as if stuck on its first line. Everything runs on the main thread, so no timing is involved.
public class FastAndSlowJava {

    static final class SlowDiary extends BaseSubscriber<Integer> {
        final List<Integer> got = new ArrayList<>();
        @Override protected void hookOnSubscribe(Subscription s) { request(1); }
        @Override protected void hookOnNext(Integer v) { got.add(v); }
    }

    static void run(String label, Sinks.Many<Integer> bell, boolean diaryHasOwnBuffer) {
        List<Integer> waiter = new ArrayList<>();
        bell.asFlux().subscribe(waiter::add);        // unbounded demand
        SlowDiary diary = new SlowDiary();
        // demand of 1, or a buffer of its own in front of the slow work
        (diaryHasOwnBuffer ? bell.asFlux().onBackpressureBuffer(64) : bell.asFlux()).subscribe(diary);
        List<String> results = new ArrayList<>();
        for (int a = 1; a <= 6; a++) results.add(a + "=" + bell.tryEmitNext(a));
        String waiterBefore = waiter.toString();
        diary.request(Long.MAX_VALUE);               // the diary keeper catches up at the end
        System.out.println(label);
        System.out.println("  tryEmitNext: " + results);
        System.out.println("  waiter had " + waiterBefore + " while the diary keeper was stuck");
        System.out.println("  waiter got " + waiter);
        System.out.println("  diary got  " + diary.got);
    }

    public static void main(String[] args) {
        run("multicast().directAllOrNothing()", Sinks.many().multicast().directAllOrNothing(), false);
        run("multicast().onBackpressureBuffer(1, false)", Sinks.many().multicast().onBackpressureBuffer(1, false), false); // one slot
        run("multicast().directBestEffort()", Sinks.many().multicast().directBestEffort(), false);
        run("onBackpressureBuffer(1, false), the diary subscribes through onBackpressureBuffer(64)",
                Sinks.many().multicast().onBackpressureBuffer(1, false), true);
    }
}
