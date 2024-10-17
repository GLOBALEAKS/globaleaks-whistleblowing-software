import {AfterViewInit, ChangeDetectorRef, Component, Inject, OnInit, Renderer2} from "@angular/core";
import {AppConfigService} from "@app/services/root/app-config.service";
import {AppDataService} from "@app/app-data.service";
import {UtilsService} from "@app/shared/services/utils.service";
import {LangChangeEvent, TranslateService} from "@ngx-translate/core";
import {NavigationEnd, Router} from "@angular/router";
import {BrowserCheckService} from "@app/shared/services/browser-check.service";
import {animate, state, style, transition, trigger} from "@angular/animations";
import {TranslationService} from "@app/services/helper/translation.service";
import {DOCUMENT} from "@angular/common";
import {AuthenticationService} from "@app/services/helper/authentication.service";

@Component({
  selector: "app-root",
  templateUrl: "./app.component.html",
  animations: [
    trigger('fadeInOut', [
      state('void', style({
        opacity: 0
      })),
      transition(':enter, :leave', animate(150)),
    ])
  ]
})
export class AppComponent implements AfterViewInit, OnInit {
  showSidebar: boolean = true;
  isNavCollapsed: boolean = true;
  showLoadingPanel = false;
  supportedBrowser = true;
  loading = false;

  constructor(@Inject(DOCUMENT) private document: Document, private renderer: Renderer2, protected browserCheckService: BrowserCheckService, private changeDetectorRef: ChangeDetectorRef, private router: Router, protected translationService: TranslationService, protected translate: TranslateService, protected appConfig: AppConfigService, protected appDataService: AppDataService, protected utilsService: UtilsService, protected authenticationService: AuthenticationService) {
    this.watchLanguage();
  }

  watchLanguage() {
    this.translate.onLangChange.subscribe((event: LangChangeEvent) => {
      document.getElementsByTagName("html")[0].setAttribute("lang", this.translate.currentLang);
    });
  }

  checkToShowSidebar() {
    this.router.events.subscribe(event => {
      if (event instanceof NavigationEnd) {
        const excludedUrls = [
          "/recipient/reports"
        ];
        const currentUrl = event.url;
        this.showSidebar = !excludedUrls.includes(currentUrl);
      }
    });
  }

  ngOnInit() {
    this.appConfig.routeChangeListener();
    this.checkToShowSidebar();
  }

  isWhistleblowerPage() {
    const temp = this.utilsService.isWhistleblowerPage(this.authenticationService, this.appDataService)
    if ((this.router.url === "/" || this.router.url === "/submission") && this.loading) {
      return true;
    } else {
      this.loading = temp;
      return this.loading;
    }
  }

  public ngAfterViewInit(): void {
    this.appDataService.showLoadingPanel$.subscribe((value) => {
      this.showLoadingPanel = value;
      this.supportedBrowser = this.browserCheckService.checkBrowserSupport();
      this.changeDetectorRef.detectChanges();
    });
  }

  protected readonly location = location;
}
