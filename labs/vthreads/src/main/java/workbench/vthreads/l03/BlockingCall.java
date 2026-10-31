package workbench.vthreads.l03;

/** A blocking call that turns one input into one output, and may throw. */
@FunctionalInterface
public interface BlockingCall<I, O> {
    O call(I input) throws Exception;
}
