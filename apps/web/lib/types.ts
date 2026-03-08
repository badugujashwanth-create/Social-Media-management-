export type ConnectorCapabilities = {
  supports_image: boolean;
  supports_link: boolean;
};

export type OAuthAccount = {
  id: number;
  platform: 'facebook' | 'linkedin' | 'x' | 'instagram';
  display_name: string | null;
  external_account_id: string;
  expires_at: string | null;
  scopes: string | null;
  meta_json: Record<string, unknown> | null;
  capabilities: ConnectorCapabilities;
  updated_at: string;
};

export type PostTarget = {
  id: number;
  oauth_account_id: number;
  platform: string;
  status: string;
  error_code: string | null;
  error_message: string | null;
  external_post_id: string | null;
  attempts: number;
  updated_at: string;
};

export type Post = {
  id: number;
  text: string;
  link_url: string | null;
  media_url: string | null;
  created_at: string;
  targets: PostTarget[];
};
