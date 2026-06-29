"use client";

import { PageHeader } from "@/components/layout/page-header";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ProfileSettings } from "@/components/settings/profile-settings";
import { AppearanceSettings } from "@/components/settings/appearance-settings";
import { GenerationSettings } from "@/components/settings/generation-settings";
import { PlaybackSettings } from "@/components/settings/playback-settings";
import { NotificationSettings } from "@/components/settings/notification-settings";
import { SecuritySettings } from "@/components/settings/security-settings";

export default function SettingsPage() {
  return (
    <>
      <PageHeader
        title="Settings"
        description="Manage your profile, generation defaults, notifications and more."
      />
      <Tabs defaultValue="profile" className="space-y-6">
        <TabsList className="flex-wrap">
          <TabsTrigger value="profile">Profile</TabsTrigger>
          <TabsTrigger value="appearance">Appearance</TabsTrigger>
          <TabsTrigger value="generation">Generation</TabsTrigger>
          <TabsTrigger value="playback">Playback &amp; export</TabsTrigger>
          <TabsTrigger value="notifications">Notifications</TabsTrigger>
          <TabsTrigger value="security">Security</TabsTrigger>
        </TabsList>
        <TabsContent value="profile" className="max-w-2xl">
          <ProfileSettings />
        </TabsContent>
        <TabsContent value="appearance" className="max-w-2xl">
          <AppearanceSettings />
        </TabsContent>
        <TabsContent value="generation" className="max-w-3xl">
          <GenerationSettings />
        </TabsContent>
        <TabsContent value="playback" className="max-w-3xl">
          <PlaybackSettings />
        </TabsContent>
        <TabsContent value="notifications" className="max-w-2xl">
          <NotificationSettings />
        </TabsContent>
        <TabsContent value="security" className="max-w-2xl">
          <SecuritySettings />
        </TabsContent>
      </Tabs>
    </>
  );
}
