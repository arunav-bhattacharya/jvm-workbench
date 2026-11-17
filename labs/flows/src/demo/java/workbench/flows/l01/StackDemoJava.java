// Java equivalent of StackDemo.kt: the hand-written push flow, with the stack printed from inside
// the collector. The collector's frame sits on top of the producer's call to emit.
package workbench.flows.l01;

public class StackDemoJava {
    interface ToyCollector<T> {
        void emit(T value);
    }

    interface ToyFlow<T> {
        void collect(ToyCollector<T> collector);
    }

    static void printStack(String label) {
        System.out.println(label + ", thread=" + Thread.currentThread().getName());
        StackTraceElement[] frames = Thread.currentThread().getStackTrace();
        for (int i = 2; i < frames.length; i++) {      // skip getStackTrace and printStack
            String cls = frames[i].getClassName().replace("workbench.flows.l01.", "");
            System.out.println("    at " + cls + "." + frames[i].getMethodName());
        }
    }

    public static void main(String[] args) {
        ToyFlow<String> dinner = collector -> collector.emit("soup");
        dinner.collect(value -> printStack("collector got " + value));
    }
}
