package workbench.performance.l06;

/**
 * A target for async-profiler: four threads run SlowFees.feeSlow for 8 seconds.
 * While it runs, attach from another terminal:  asprof -d 5 -f cpu.html <pid>
 */
public class ProfileMe {
    public static void main(String[] args) throws Exception {
        int seconds = args.length > 0 ? Integer.parseInt(args[0]) : 8;
        System.out.println("pid " + ProcessHandle.current().pid() + ", running for " + seconds + " s");
        System.out.println("attach with: asprof -d 5 -f cpu.html " + ProcessHandle.current().pid());
        SlowFees.hammer(4, System.nanoTime() + seconds * 1_000_000_000L);
        System.out.println("done");
    }
}
