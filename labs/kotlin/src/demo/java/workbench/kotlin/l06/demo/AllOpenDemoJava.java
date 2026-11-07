package workbench.kotlin.l06.demo;

/**
 * Java twin of AllOpenDemo.kt. Java classes are open unless you write final, so Java can extend the
 * Kotlin class only because all-open removed its final. Remove the marker and javac says:
 * "cannot inherit from final SettlementService".
 */
public class AllOpenDemoJava {

    static final class AuditedSettlementService extends SettlementService {
        @Override
        public String settle(String batch) {
            System.out.println("  audit: settling " + batch);
            return super.settle(batch);
        }
    }

    public static void main(String[] args) {
        SettlementService service = new AuditedSettlementService();
        System.out.println(service.settle("batch-17"));
        AllOpenDemoKt.describe(PlainHelper.class);
    }
}
