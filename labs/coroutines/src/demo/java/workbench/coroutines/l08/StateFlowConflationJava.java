// Java equivalent of StateFlowConflation.kt with Reactor: a sink that replays its latest value,
// distinctUntilChanged for the equality rule, and onBackpressureLatest so a slow subscriber only
// gets the newest value. StateFlow does all three by itself.
package workbench.coroutines.l08;

import reactor.core.Disposable;
import reactor.core.publisher.Sinks;
import reactor.core.scheduler.Schedulers;

public class StateFlowConflationJava {
    record Menu(String soup) {}

    public static void main(String[] args) throws InterruptedException {
        Sinks.Many<Menu> board = Sinks.many().replay().latestOrDefault(new Menu("tomato"));
        Disposable hall = board.asFlux()
            .distinctUntilChanged()
            .onBackpressureLatest()
            .publishOn(Schedulers.single(), 1)   // request one value at a time
            .subscribe(menu -> {
                System.out.println("the board in the hall shows " + menu.soup() + " soup");
                sleep(100); // chalking up the board is slow
            });
        Thread.sleep(20);
        // the cook changes her mind three times while the board is being chalked up
        board.tryEmitNext(new Menu("leek"));
        board.tryEmitNext(new Menu("pea"));
        board.tryEmitNext(new Menu("onion"));
        Thread.sleep(250);
        System.out.println("setting an equal menu again (a new object, same fields)");
        board.tryEmitNext(new Menu("onion"));
        Thread.sleep(150);
        hall.dispose();
    }

    static void sleep(long ms) { try { Thread.sleep(ms); } catch (InterruptedException e) { Thread.currentThread().interrupt(); } }
}
