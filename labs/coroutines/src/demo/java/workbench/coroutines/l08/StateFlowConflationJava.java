// Java equivalent of StateFlowConflation.kt with Reactor: a sink that replays its latest value,
// distinctUntilChanged for the equality rule, and onBackpressureLatest so a slow subscriber only
// gets the newest value. StateFlow does all three by itself.
package workbench.coroutines.l08;

import reactor.core.Disposable;
import reactor.core.publisher.Sinks;
import reactor.core.scheduler.Schedulers;

public class StateFlowConflationJava {
    record Rate(String pair, double mid) {}

    public static void main(String[] args) throws InterruptedException {
        Sinks.Many<Rate> eurUsd = Sinks.many().replay().latestOrDefault(new Rate("EUR/USD", 1.0809));
        Disposable dashboard = eurUsd.asFlux()
            .distinctUntilChanged()
            .onBackpressureLatest()
            .publishOn(Schedulers.single(), 1)   // request one value at a time
            .subscribe(rate -> {
                System.out.println("dashboard shows " + rate.mid());
                sleep(100); // rendering is slow
            });
        Thread.sleep(20);
        // three ticks arrive while the dashboard is busy rendering the first value
        eurUsd.tryEmitNext(new Rate("EUR/USD", 1.0811));
        eurUsd.tryEmitNext(new Rate("EUR/USD", 1.0812));
        eurUsd.tryEmitNext(new Rate("EUR/USD", 1.0813));
        Thread.sleep(250);
        System.out.println("setting an equal rate again (a new object, same fields)");
        eurUsd.tryEmitNext(new Rate("EUR/USD", 1.0813));
        Thread.sleep(150);
        dashboard.dispose();
    }

    static void sleep(long ms) { try { Thread.sleep(ms); } catch (InterruptedException e) { Thread.currentThread().interrupt(); } }
}
