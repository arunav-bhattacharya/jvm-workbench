package workbench.vthreads.l02;

/** What a fiber hands back to the scheduler when it stops running: "wake me in N ms" or "I'm finished". */
public sealed interface Step permits Step.Sleep, Step.Done {
    record Sleep(long millis) implements Step {}

    record Done() implements Step {}

    static Step sleep(long millis) {
        return new Sleep(millis);
    }

    static Step done() {
        return new Done();
    }
}
