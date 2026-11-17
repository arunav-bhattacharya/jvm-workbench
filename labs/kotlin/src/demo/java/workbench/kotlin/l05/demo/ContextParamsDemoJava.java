package workbench.kotlin.l05.demo;

/**
 * Java twin of ContextParamsDemo.kt. Java has no context parameters. To Java they are ordinary
 * leading parameters: context parameters first, then the extension receiver, then the rest.
 */
public class ContextParamsDemoJava {
    public static void main(String[] args) {
        Logbook console = System.out::println;
        Shift shift = new Shift("java");

        // takeIn(Logbook, Shift, Job, String)
        System.out.println(ContextParamsDemoKt.takeIn(console, shift, new Job("flyer.pdf", 250), "laser-1"));
        // check(Logbook, Shift, Job receiver, String printer)
        System.out.println(ContextParamsDemoKt.check(console, shift, new Job("posters.pdf", 5_000), "laser-2"));
        // remark(Logbook, String)
        ContextParamsDemoKt.remark(console, "called from Java");
    }
}
