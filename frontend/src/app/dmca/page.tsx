"use client";

import * as React from "react";
import { useSearchParams } from "next/navigation";
import { toast } from "sonner";

import { submitDmcaRequest, type DmcaTargetType } from "@/lib/dmca";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const TARGET_TYPES: { value: DmcaTargetType; label: string }[] = [
  { value: "blog_post", label: "Blog post" },
  { value: "blog_comment", label: "Blog comment" },
  { value: "listing", label: "Marketplace listing" },
  { value: "listing_comment", label: "Listing comment" },
];

function DmcaForm() {
  const searchParams = useSearchParams();
  const prefillType = searchParams.get("target_type") as DmcaTargetType | null;
  const prefillId = searchParams.get("target_id");
  const locked = !!(prefillType && prefillId);

  const [claimantName, setClaimantName] = React.useState("");
  const [claimantEmail, setClaimantEmail] = React.useState("");
  const [targetType, setTargetType] = React.useState<DmcaTargetType>(
    prefillType ?? "blog_post",
  );
  const [targetId, setTargetId] = React.useState(prefillId ?? "");
  const [workDescription, setWorkDescription] = React.useState("");
  const [affirmed, setAffirmed] = React.useState(false);
  const [signature, setSignature] = React.useState("");
  const [submitting, setSubmitting] = React.useState(false);
  const [submitted, setSubmitted] = React.useState(false);

  async function submit() {
    if (
      !claimantName.trim() ||
      !claimantEmail.trim() ||
      !targetId.trim() ||
      !workDescription.trim() ||
      !signature.trim()
    ) {
      toast.error("Fill in every field.");
      return;
    }
    if (!affirmed) {
      toast.error("You must affirm the good-faith statement.");
      return;
    }
    setSubmitting(true);
    try {
      await submitDmcaRequest({
        claimant_name: claimantName.trim(),
        claimant_email: claimantEmail.trim(),
        target_type: targetType,
        target_id: targetId.trim(),
        work_description: workDescription.trim(),
        good_faith_statement: affirmed,
        signature: signature.trim(),
      });
      setSubmitted(true);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Submission failed.");
    } finally {
      setSubmitting(false);
    }
  }

  if (submitted) {
    return (
      <div className="mx-auto w-full max-w-[600px] px-4 py-24 text-center">
        <h1 className="text-2xl font-bold">Notice submitted</h1>
        <p className="mt-3 text-muted-foreground">
          Thanks — our team will review your takedown notice and follow up by
          email if we need anything else.
        </p>
      </div>
    );
  }

  return (
    <div className="mx-auto w-full max-w-[600px] px-4 py-12">
      <h1 className="text-3xl font-extrabold tracking-tight">
        Copyright takedown notice
      </h1>
      <p className="mt-2 text-sm text-muted-foreground">
        Submit a formal DMCA notice for content you believe infringes your
        copyright. No account required.
      </p>

      <div className="mt-8 space-y-4">
        <div>
          <label className="mb-1 block text-sm font-medium">Your name</label>
          <Input value={claimantName} onChange={(e) => setClaimantName(e.target.value)} />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium">Your email</label>
          <Input
            type="email"
            value={claimantEmail}
            onChange={(e) => setClaimantEmail(e.target.value)}
          />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="mb-1 block text-sm font-medium">Content type</label>
            <Select
              value={targetType}
              onValueChange={(v) => setTargetType(v as DmcaTargetType)}
              disabled={locked}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {TARGET_TYPES.map((t) => (
                  <SelectItem key={t.value} value={t.value}>
                    {t.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">Content ID</label>
            <Input
              value={targetId}
              onChange={(e) => setTargetId(e.target.value)}
              disabled={locked}
              placeholder="From the report link or support"
            />
          </div>
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium">
            Description of the copyrighted work
          </label>
          <Textarea
            value={workDescription}
            onChange={(e) => setWorkDescription(e.target.value)}
            className="min-h-24"
            placeholder="What is the original work, and how does this content infringe it?"
          />
        </div>
        <label className="flex items-start gap-2 text-sm">
          <input
            type="checkbox"
            className="mt-1"
            checked={affirmed}
            onChange={(e) => setAffirmed(e.target.checked)}
          />
          <span>
            I have a good-faith belief that the use described above is not
            authorized by the copyright owner, its agent, or the law, and,
            under penalty of perjury, I am authorized to act on behalf of the
            copyright owner.
          </span>
        </label>
        <div>
          <label className="mb-1 block text-sm font-medium">
            Electronic signature (type your full name)
          </label>
          <Input value={signature} onChange={(e) => setSignature(e.target.value)} />
        </div>
        <Button onClick={submit} loading={submitting} className="w-full">
          Submit notice
        </Button>
      </div>
    </div>
  );
}

export default function DmcaPage() {
  return (
    <React.Suspense>
      <DmcaForm />
    </React.Suspense>
  );
}
