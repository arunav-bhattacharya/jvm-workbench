package workbench.bytecode.l07;

import net.bytebuddy.agent.ByteBuddyAgent;
import net.bytebuddy.agent.builder.AgentBuilder;
import net.bytebuddy.asm.Advice;

import java.lang.instrument.Instrumentation;

import static net.bytebuddy.matcher.ElementMatchers.is;
import static net.bytebuddy.matcher.ElementMatchers.named;

/** Attach an agent to this running JVM and change a loaded class under a live object. */
public class LiveRetransformDemo {
    public static final class FxClock {           // final: lesson 5's subclass proxies couldn't touch it
        public String now() { return "tick"; }
    }

    public static class TimingAdvice {
        @Advice.OnMethodEnter
        static long enter() {
            return System.nanoTime();             // copied to the start of now()
        }

        @Advice.OnMethodExit(onThrowable = Throwable.class)
        static void exit(@Advice.Origin("#t.#m") String where, @Advice.Enter long t0) {
            System.out.println("  [advice] " + where + " took " + (System.nanoTime() - t0) + " ns");
        }
    }

    public static void main(String[] args) throws Exception {
        if (args.length > 0) {                    // -Pargs=allowed or -Pargs=blocked
            relaunch(args[0]);
            return;
        }
        FxClock clock = new FxClock();
        System.out.println("before: " + clock.now());

        Instrumentation inst = ByteBuddyAgent.install();   // self-attach: JEP 451 warns unless allowed
        System.out.println("retransform supported: " + inst.isRetransformClassesSupported());
        new AgentBuilder.Default()
                .disableClassFormatChanges()
                .with(AgentBuilder.RedefinitionStrategy.RETRANSFORMATION)
                .type(is(FxClock.class))
                .transform((builder, type, loader, module, domain) ->
                        builder.visit(Advice.to(TimingAdvice.class).on(named("now"))))
                .installOn(inst);

        System.out.println("after:  " + clock.now() + "   (the same object, no restart)");
    }

    /** Runs this demo again in a child JVM with dynamic agent loading explicitly allowed or blocked. */
    static void relaunch(String mode) throws Exception {
        String flag = mode.equals("blocked") ? "-XX:-EnableDynamicAgentLoading" : "-XX:+EnableDynamicAgentLoading";
        String java = ProcessHandle.current().info().command().orElse("java");
        Process child = new ProcessBuilder(java, flag, "-cp", System.getProperty("java.class.path"),
                LiveRetransformDemo.class.getName())
                .redirectErrorStream(true)
                .start();
        System.out.println("child JVM with " + flag + ":");
        child.getInputStream().transferTo(System.out);
        System.out.println("child exited with " + child.waitFor());
    }
}
