import { Log } from '@microsoft/sp-core-library';
import { BaseApplicationCustomizer } from '@microsoft/sp-application-base';
import { PlaceholderContent, PlaceholderName } from '@microsoft/sp-application-base';

import * as strings from 'SpfxHeaderfooterApplicationCustomizerStrings';

const LOG_SOURCE: string = 'SpfxHeaderfooterApplicationCustomizer';

/**
 * If your command set uses the ClientSideComponentProperties JSON input,
 * it will be deserialized into the BaseExtension.properties object.
 * You can define an interface to describe it.
 */
export interface ISpfxHeaderfooterApplicationCustomizerProperties {
  // This is an example; replace with your own property
  testMessage: string;
}

/** A Custom Action which can be run during execution of a Client Side Application */
export default class SpfxHeaderfooterApplicationCustomizer
  extends BaseApplicationCustomizer<ISpfxHeaderfooterApplicationCustomizerProperties> {

  private _headerPlaceholder: PlaceholderContent | undefined;
  private _footerPlaceholder: PlaceholderContent | undefined;

  public onInit(): Promise<void> {
    Log.info(LOG_SOURCE, `Initialized ${strings.Title}`);

    this.context.placeholderProvider.changedEvent.add(this, this._renderPlaceholders);
    this._renderPlaceholders();
    return Promise.resolve();
  }

  private _renderPlaceholders(): void {
    // Header
    if (!this._headerPlaceholder) {
      this._headerPlaceholder = this.context.placeholderProvider.tryCreateContent(PlaceholderName.Top, { onDispose: this._onDisposeHeader });
      if (this._headerPlaceholder && this._headerPlaceholder.domElement) {
        this._headerPlaceholder.domElement.innerHTML = `<div style="height:40px;display:flex;align-items:center;justify-content:center;font-size:18px;font-weight:bold;background:#f3f3f3;">Hallo Infinity</div>`;
      }
    }
    // Footer
    if (!this._footerPlaceholder) {
      this._footerPlaceholder = this.context.placeholderProvider.tryCreateContent(PlaceholderName.Bottom, { onDispose: this._onDisposeFooter });
      if (this._footerPlaceholder && this._footerPlaceholder.domElement) {
        this._footerPlaceholder.domElement.innerHTML = `<div style="height:40px;display:flex;align-items:center;justify-content:center;background:#f3f3f3;"><button style='height:32px;padding:0 16px;font-size:16px;cursor:pointer;' onclick="window.open('https://www.cubido.at','_blank')">welcome</button></div>`;
      }
    }
  }

  private _onDisposeHeader(): void {
    // ...existing code...
  }

  private _onDisposeFooter(): void {
    // ...existing code...
  }
}
