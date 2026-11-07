package workbench.modernjava.l02;

import workbench.modernjava.l02.PaymentMethod.BankTransfer;
import workbench.modernjava.l02.PaymentMethod.Card;
import workbench.modernjava.l02.PaymentMethod.PartnerMethod;
import workbench.modernjava.l02.PaymentMethod.Sepa;
import workbench.modernjava.l02.PaymentMethod.Swift;
import workbench.modernjava.l02.PaymentMethod.Wallet;

public final class Settlement {
    private Settlement() {}

    public static int daysToSettle(PaymentMethod method) {
        return switch (method) {                   // no default: a new method breaks the build here
            case Card c -> 2;
            case Sepa s -> 1;
            case Swift s -> 3;
            case Wallet w -> 0;
            case PartnerMethod p -> p.settlementDays();   // covers every partner class, known or not
        };
    }

    public static String rail(PaymentMethod method) {
        return switch (method) {
            case Card c -> "card";
            case BankTransfer t -> "bank";         // BankTransfer is sealed, so this one case covers Sepa and Swift
            case Wallet w -> "wallet";
            case PartnerMethod p -> "partner:" + p.partnerId();
        };
    }
}
