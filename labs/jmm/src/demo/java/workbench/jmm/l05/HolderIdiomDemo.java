package workbench.jmm.l05;

/** When does each singleton get built? Watch the order of the lines. */
public class HolderIdiomDemo {
    // eager: built when the class is initialized, by the first use of anything static in it
    static final class EagerBins {
        static final EagerBins INSTANCE = new EagerBins();
        private EagerBins() { System.out.println("     EagerBins built"); }
        static int tableSize() { return 3; }
    }

    // holder idiom: built when Holder is initialized, by the first call to instance()
    static final class LazyBins {
        private LazyBins() { System.out.println("     LazyBins built"); }
        private static final class Holder {
            static final LazyBins INSTANCE = new LazyBins();
        }
        static LazyBins instance() { return Holder.INSTANCE; }
        static int tableSize() { return 3; }
    }

    // enum singleton: built when the enum class is initialized
    enum EnumBins {
        INSTANCE;
        EnumBins() { System.out.println("     EnumBins.INSTANCE built"); }
        static int tableSize() { return 3; }
    }

    public static void main(String[] args) {
        System.out.println("1. call EagerBins.tableSize()");
        EagerBins.tableSize();
        System.out.println("2. call LazyBins.tableSize()");
        LazyBins.tableSize();
        System.out.println("3. call LazyBins.instance()");
        LazyBins.instance();
        System.out.println("4. call LazyBins.instance() again");
        LazyBins.instance();
        System.out.println("5. call EnumBins.tableSize()");
        EnumBins.tableSize();
    }
}
